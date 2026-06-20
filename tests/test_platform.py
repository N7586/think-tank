import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.arf import ARFAsset, Subscription
from app.models.marketplace import MarketplaceOffer
from app.models.transaction import Transaction


class TestRunner:
    def __init__(self):
        self.app = create_app()
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.passed = 0
        self.failed = 0
        self.errors = []

    def test(self, name, condition, detail=""):
        if condition:
            self.passed += 1
            print(f"  ✅ {name}")
        else:
            self.failed += 1
            self.errors.append(f"{name}: {detail}")
            print(f"  ❌ {name} {detail}")

    def run_all(self):
        print("=" * 60)
        print("  TESTS COMPLETS - PLATEFORME TSI")
        print("=" * 60)

        with self.app.app_context():
            db.create_all()
            self._test_public_routes()
            self._test_auth()
            self._test_admin()
            self._test_arf()
            self._test_marketplace()
            self._test_simulator()
            self._test_payment()
            self._test_models()

        print()
        print("=" * 60)
        total = self.passed + self.failed
        print(f"  RESULTATS: {self.passed}/{total} passes, {self.failed} echecs")
        if self.errors:
            print()
            print("  Erreurs:")
            for e in self.errors:
                print(f"    - {e}")
        print("=" * 60)
        return self.failed == 0

    def _test_public_routes(self):
        print("\n--- ROUTES PUBLIQUES ---")
        routes = [
            ("/", 200, "Accueil"),
            ("/about", 200, "A propos"),
            ("/contact", 200, "Contact"),
            ("/auth/login", 200, "Connexion"),
            ("/auth/register", 200, "Inscription"),
            ("/arf/", 200, "Catalogue ARF"),
            ("/marketplace/", 200, "Marketplace"),
            ("/simulator/", 200, "Simulateur"),
            ("/blog/", 200, "Blog"),
            ("/auth/tsi-admin-secret-2024/register", 200, "Admin Secret Register"),
            ("/auth/wrong-secret/register", 302, "Mauvais Secret"),
        ]
        for route, expected, desc in routes:
            resp = self.client.get(route)
            self.test(desc, resp.status_code == expected, f"({resp.status_code} != {expected})")

    def _test_auth(self):
        print("\n--- AUTHENTIFICATION ---")

        resp = self.client.post("/auth/register", data={
            "first_name": "Jean",
            "last_name": "Dupont",
            "email": "jean@test.com",
            "phone": "+22501010101",
            "language": "fr",
            "password": "test1234",
            "confirm_password": "test1234",
        }, follow_redirects=False)
        self.test("Inscription utilisateur", resp.status_code in [302, 200], f"({resp.status_code})")

        resp = self.client.post("/auth/login", data={
            "email": "jean@test.com",
            "password": "test1234",
            "remember": "y",
        }, follow_redirects=False)
        self.test("Login utilisateur", resp.status_code == 302, f"({resp.status_code})")

        resp = self.client.get("/member/dashboard")
        self.test("Acces member dashboard", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.get("/member/portfolio")
        self.test("Acces portfolio", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.get("/member/transactions")
        self.test("Acces transactions", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.get("/payment/history")
        self.test("Acces historique paiements", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.get("/auth/logout", follow_redirects=False)
        self.test("Logout", resp.status_code == 302, f"({resp.status_code})")

    def _test_admin(self):
        print("\n--- ADMINISTRATION ---")

        resp = self.client.post("/auth/tsi-admin-secret-2024/register", data={
            "first_name": "Admin",
            "last_name": "TSI",
            "email": "admin@tsi.com",
            "phone": "+22502020202",
            "password": "admin1234",
            "confirm_password": "admin1234",
        }, follow_redirects=False)
        self.test("Inscription admin", resp.status_code in [302, 200], f"({resp.status_code})")

        resp = self.client.post("/auth/login", data={
            "email": "admin@tsi.com",
            "password": "admin1234",
        }, follow_redirects=False)
        self.test("Login admin", resp.status_code == 302, f"({resp.status_code})")

        resp = self.client.post("/auth/admin/verify", data={"code": "12345"}, follow_redirects=False)
        self.test("Verification code admin", resp.status_code == 302, f"({resp.status_code})")

        resp = self.client.get("/admin/dashboard")
        self.test("Dashboard admin", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.get("/admin/users")
        self.test("Liste utilisateurs", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.get("/admin/users/2")
        self.test("Detail utilisateur", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.get("/admin/users/2/edit")
        self.test("Formulaire edit user", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.post("/admin/users/2/toggle-status", follow_redirects=False)
        self.test("Toggle status user", resp.status_code == 302, f"({resp.status_code})")

        resp = self.client.post("/admin/users/2/toggle-status", follow_redirects=False)
        self.test("Toggle status user (restore)", resp.status_code == 302, f"({resp.status_code})")

        resp = self.client.get("/arf/admin/list")
        self.test("Admin ARF list", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.get("/marketplace/admin/list")
        self.test("Admin Marketplace list", resp.status_code == 200, f"({resp.status_code})")

        self.client.get("/auth/logout")

    def _test_arf(self):
        print("\n--- ARF ---")

        self.client.post("/auth/login", data={
            "email": "admin@tsi.com",
            "password": "admin1234",
        })
        self.client.post("/auth/admin/verify", data={"code": "12345"})

        resp = self.client.get("/arf/admin/create")
        self.test("Formulaire creation ARF", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.post("/arf/admin/create", data={
            "name": "ARF Agro Cote d'Ivoire",
            "description": "Fonds d'investissement agro-industrie en Cote d'Ivoire pour le developpement local.",
            "sector": "agro-industrie",
            "country": "Cote d'Ivoire",
            "total_value": "1000000",
            "unit_price": "100",
            "expected_return": "8.5",
            "risk_level": "low",
        }, follow_redirects=False)
        self.test("Creation ARF", resp.status_code == 302, f"({resp.status_code})")

        resp = self.client.get("/arf/")
        self.test("Catalogue ARF (1 ARF)", resp.status_code == 200 and b"ARF Agro" in resp.data, f"(status={resp.status_code})")

        resp = self.client.get("/arf/1")
        self.test("Detail ARF", resp.status_code == 200 and b"ARF Agro" in resp.data, f"(status={resp.status_code})")

        resp = self.client.get("/arf/admin/list")
        self.test("Admin ARF list (1 ARF)", resp.status_code == 200 and b"ARF Agro" in resp.data, f"(status={resp.status_code})")

        resp = self.client.get("/arf/admin/1/edit")
        self.test("Formulaire edit ARF", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.post("/arf/admin/1/edit", data={
            "name": "ARF Agro CI V2",
            "description": "Fonds d'investissement agro-industrie mis a jour.",
            "sector": "agro-industrie",
            "country": "Cote d'Ivoire",
            "total_value": "2000000",
            "unit_price": "200",
            "expected_return": "9.0",
            "risk_level": "low",
        }, follow_redirects=False)
        self.test("Update ARF", resp.status_code == 302, f"({resp.status_code})")

        self.client.get("/auth/logout")

    def _test_marketplace(self):
        print("\n--- MARKETPLACE ---")

        self.client.post("/auth/login", data={
            "email": "jean@test.com",
            "password": "test1234",
        })

        resp = self.client.get("/marketplace/create")
        self.test("Formulaire creation offre", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.post("/marketplace/create", data={
            "title": "Marche public route nationale",
            "description": "Construction d'une route nationale de 50km.",
            "contract_type": "travaux",
            "value": "5000000",
            "deadline": "2025-12-31",
        }, follow_redirects=False)
        self.test("Creation offre marketplace", resp.status_code in [302, 200], f"({resp.status_code})")

        resp = self.client.get("/marketplace/")
        self.test("Catalogue marketplace", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.get("/marketplace/1")
        self.test("Detail offre", resp.status_code == 200, f"({resp.status_code})")

        resp = self.client.get("/marketplace/my-offers")
        self.test("Mes offres", resp.status_code == 200, f"({resp.status_code})")

        self.client.get("/auth/logout")

    def _test_simulator(self):
        print("\n--- SIMULATEUR ---")

        resp = self.client.post("/simulator/", data={
            "investment": "1000",
            "unit_price": "100",
            "expected_return": "8.5",
            "duration": "12",
        })
        has_result = b"1,085" in resp.data or b"Valeur finale" in resp.data
        self.test("Simulateur calcul", resp.status_code == 200 and has_result, f"(status={resp.status_code})")

    def _test_payment(self):
        print("\n--- PAIEMENT ---")

        self.client.post("/auth/login", data={
            "email": "jean@test.com",
            "password": "test1234",
        })

        resp = self.client.get("/payment/history")
        self.test("Historique paiements", resp.status_code == 200, f"({resp.status_code})")

        self.client.get("/auth/logout")

    def _test_models(self):
        print("\n--- MODELES / BDD ---")

        users = User.query.all()
        self.test("Users en BDD", len(users) >= 2, f"({len(users)} users)")

        admins = User.query.filter_by(role='admin').count()
        self.test("Au moins 1 admin", admins >= 1, f"({admins})")

        regular = User.query.filter_by(role='user').count()
        self.test("Au moins 1 utilisateur", regular >= 1, f"({regular})")

        arfs = ARFAsset.query.all()
        self.test("ARF en BDD", len(arfs) >= 1, f"({len(arfs)} ARF)")

        offers = MarketplaceOffer.query.all()
        self.test("Offres marketplace", len(offers) >= 1, f"({len(offers)} offres)")

        user = User.query.filter_by(email='jean@test.com').first()
        self.test("Utilisateur jean@test.com existe", user is not None)
        if user:
            self.test("Jean est bien role='user'", user.role == 'user', f"(role={user.role})")
            self.test("Jean est actif", user.is_active == True)
            self.test("Jean prenom correct", user.first_name == 'Jean')

        admin = User.query.filter_by(email='admin@tsi.com').first()
        self.test("Admin admin@tsi.com existe", admin is not None)
        if admin:
            self.test("Admin est bien role='admin'", admin.role == 'admin', f"(role={admin.role})")


if __name__ == '__main__':
    runner = TestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
