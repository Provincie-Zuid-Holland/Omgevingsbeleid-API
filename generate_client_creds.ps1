$env:FLASK_APP="server"
$cl_id = Read_Host -Promt "Client identifier:"
flask generate-client-creds $cl_id
Read_Host -Promt "Press any key to exit..."