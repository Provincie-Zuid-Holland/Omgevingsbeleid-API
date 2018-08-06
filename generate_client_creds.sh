export FLASK_APP=server.py
export FLASK_ENV=development
echo Client identifier:
read cl_id
flask generate_client_creds $cl_id