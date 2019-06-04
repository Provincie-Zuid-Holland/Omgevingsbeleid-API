$env:FLASK_APP="server"
$cl_id = Read-Host -Prompt "Client identifier:"
flask generate-client-creds $cl_id
Read_Host -Prompt "Press any key to exit..."