


# class FixtureDataFactory:
#     def __init__(self, db: Session):
#         self._db = db
#         self.users = []

#     def populate_users_db(self):
#         for user_data in self.create_users():
#             user = self._create_user(user_data)
#             self._db.add(user)
#             self.users.append(user)
#         self._db.commit()

#     def create_users(self):
#         for user_data in self._user_data():
#             user = self._create_user(user_data)
#             self.users.append(user)

#     def _create_user(self, user_data):
#         user_obj = UsersTable(**user_data)
#         return user_obj

#     def _user_data(self):
#         return [
#             {
#                 "UUID": UUID("11111111-0000-0000-0000-000000000001"),
#                 "Gebruikersnaam": "Anton",
#                 "Email": "test@example.com",
#                 "Rol": "Superuser",
#                 "Status": "Actief",
#                 "Wachtwoord": get_password_hash("password"),
#             },
#             {
#                 "UUID": UUID("11111111-0000-0000-0000-000000000002"),
#                 "Gebruikersnaam": "Bert",
#                 "Email": "b@example.com",
#                 "Rol": "Ambtelijk opdrachtgever",
#                 "Status": "Actief",
#                 "Wachtwoord": get_password_hash("password"),
#             },
#             {
#                 "UUID": UUID("11111111-0000-0000-0000-000000000003"),
#                 "Gebruikersnaam": "Cees",
#                 "Email": "c@example.com",
#                 "Rol": "Behandelend Ambtenaar",
#                 "Status": "Actief",
#                 "Wachtwoord": get_password_hash("password"),
#             },
#             {
#                 "UUID": UUID("11111111-0000-0000-0000-000000000004"),
#                 "Gebruikersnaam": "Daniel",
#                 "Email": "d@example.com",
#                 "Rol": "Beheerder",
#                 "Status": "Actief",
#                 "Wachtwoord": get_password_hash("password"),
#             },
#             {
#                 "UUID": UUID("11111111-0000-0000-0000-000000000005"),
#                 "Gebruikersnaam": "Emma",
#                 "Email": "e@example.com",
#                 "Rol": "Portefeuillehouder",
#                 "Status": "Actief",
#                 "Wachtwoord": get_password_hash("password"),
#             },
#             {
#                 "UUID": UUID("11111111-0000-0000-0000-000000000006"),
#                 "Gebruikersnaam": "Fred",
#                 "Email": "f@example.com",
#                 "Rol": "Test runner",
#                 "Status": "Actief",
#                 "Wachtwoord": get_password_hash("password"),
#             },
#             {
#                 "UUID": UUID("11111111-0000-0000-0000-000000000007"),
#                 "Gebruikersnaam": "Gerald",
#                 "Email": "g@example.com",
#                 "Rol": "Tester",
#                 "Status": "Actief",
#                 "Wachtwoord": get_password_hash("password"),
#             },
#         ]
