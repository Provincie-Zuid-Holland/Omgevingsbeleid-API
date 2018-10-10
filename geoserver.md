# Geoserver installatie PZH
 
 Hieronder volgen de stappen waarmee geoserver kan worden ingesteld zodat deze goed werkt met de API. Dit document is geschreven met geoserver 2.14.0 als doel.

 ## 'Gevaarlijke' symbolen toestaan
Maak in de root van je website (IIS > Explore) een file gemaand web.config aan en plak daarin het volgende:
 ```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
    </system.webServer>
	<system.web>
		<httpRuntime requestPathInvalidCharacters="&lt;,&gt;,%,&amp;,\,?" />
    </system.web>
</configuration>

 ```
 Run hierna `iisreset`.
