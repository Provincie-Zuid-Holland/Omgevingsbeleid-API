### Beleidsrelaties 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Van_Beleidskeuze | UUID | Niet: ['00000000-0000-0000-0000-000000000000'], | True |
|Naar_Beleidskeuze | UUID | Niet: ['00000000-0000-0000-0000-000000000000'], | True |
|Titel | String | HTML Validatie, | True |
|Omschrijving | String | HTML Validatie, | False |
|Status | String | Geldig: ['Open', 'Akkoord', 'NietAkkoord', 'Verbroken'], | True |
|Aanvraag_Datum | DateTime |  | True |
|Datum_Akkoord | DateTime |  | False |

### Beleidsmodules 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Titel | String |  | True |
|Besluit_Datum | DateTime |  | False |
|Maatregelen | Nested |  | False |
|Beleidskeuzes | Nested |  | False |

### Beleidskeuzes 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Eigenaar_1 | UUID |  | False |
|Eigenaar_2 | UUID |  | False |
|Portefeuillehouder_1 | UUID |  | False |
|Portefeuillehouder_2 | UUID |  | False |
|Opdrachtgever | UUID |  | False |
|Status | String | Geldig: ['Definitief ontwerp GS', 'Definitief ontwerp GS concept', 'Definitief ontwerp PS', 'Niet-Actief', 'Ontwerp GS', 'Ontwerp GS Concept', 'Ontwerp in inspraak', 'Ontwerp PS', 'Uitgecheckt', 'Vastgesteld', 'Vigerend', 'Vigerend gearchiveerd'], | True |
|Titel | String |  | True |
|Omschrijving_Keuze | String | HTML Validatie, | False |
|Omschrijving_Werking | String | HTML Validatie, | False |
|Aanleiding | String | HTML Validatie, | False |
|Afweging | String | HTML Validatie, | False |
|Provinciaal_Belang | String | HTML Validatie, | False |
|Weblink | String | HTML Validatie, | False |
|Besluitnummer | String |  | False |
|Tags | String |  | False |
|Aanpassing_Op | UUID |  | False |
|Ambities | Nested |  | False |
|Belangen | Nested |  | False |
|Beleidsdoelen | Nested |  | False |
|Beleidsprestaties | Nested |  | False |
|Beleidsregels | Nested |  | False |
|Maatregelen | Nested |  | False |
|Themas | Nested |  | False |
|Verordeningen | Nested |  | False |
|Werkingsgebieden | Nested |  | False |
|Ref_Beleidsmodules | Nested |  | False |

### Ambities 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Titel | String | HTML Validatie, | True |
|Omschrijving | String | HTML Validatie, | False |
|Weblink | String |  | False |
|Ref_Beleidskeuzes | Nested |  | False |

### Belangen 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Titel | String |  | True |
|Omschrijving | String | HTML Validatie, | False |
|Weblink | String |  | False |
|Type | String | Geldig: ['Nationaal Belang', 'Wettelijke Taak & Bevoegdheid'], | False |
|Ref_Beleidskeuzes | Nested |  | False |

### Beleidsdoelen 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Titel | String | HTML Validatie, | True |
|Omschrijving | String | HTML Validatie, | False |
|Weblink | String |  | False |
|Ref_Beleidskeuzes | Nested |  | False |

### Beleidsprestaties 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Titel | String | HTML Validatie, | True |
|Omschrijving | String | HTML Validatie, | False |
|Weblink | String |  | False |
|Ref_Beleidskeuzes | Nested |  | False |

### Beleidsregels 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Titel | String | HTML Validatie, | True |
|Omschrijving | String | HTML Validatie, | False |
|Weblink | String |  | False |
|Externe_URL | String |  | False |
|Ref_Beleidskeuzes | Nested |  | False |

### Maatregelen 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Eigenaar_1 | UUID |  | False |
|Eigenaar_2 | UUID |  | False |
|Portefeuillehouder_1 | UUID |  | False |
|Portefeuillehouder_2 | UUID |  | False |
|Opdrachtgever | UUID |  | False |
|Titel | String | HTML Validatie, | True |
|Omschrijving | String | HTML Validatie, | False |
|Toelichting | String | HTML Validatie, | False |
|Toelichting_Raw | String |  | False |
|Status | String | Geldig: ['Definitief ontwerp GS', 'Definitief ontwerp GS concept', 'Definitief ontwerp PS', 'Niet-Actief', 'Ontwerp GS', 'Ontwerp GS Concept', 'Ontwerp in inspraak', 'Ontwerp PS', 'Uitgecheckt', 'Vastgesteld', 'Vigerend', 'Vigerend gearchiveerd'], | False |
|Weblink | String |  | False |
|Gebied | UUID |  | False |
|Gebied_Duiding | String | Geldig: ['Indicatief', 'Exact'], | False |
|Tags | String |  | False |
|Aanpassing_Op | UUID |  | False |
|Ref_Beleidskeuzes | Nested |  | False |
|Ref_Beleidsmodules | Nested |  | False |

### Themas 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Titel | String | HTML Validatie, | True |
|Omschrijving | String | HTML Validatie, | False |
|Weblink | String |  | False |
|Ref_Beleidskeuzes | Nested |  | False |

### Werkingsgebieden 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Werkingsgebied | String |  | True |
|symbol | String |  | False |

### Verordeningen 
| Veldnaam | Type | Opmerking | Verplicht | 
 | --- | --- | --- | --- | 
|ID | Integer |  | False |
|UUID | UUID |  | True |
|Begin_Geldigheid | DateTime |  | False |
|Eind_Geldigheid | DateTime |  | False |
|Created_By | UUID |  | True |
|Created_Date | DateTime |  | True |
|Modified_By | UUID |  | True |
|Modified_Date | DateTime |  | True |
|Eigenaar_1 | UUID |  | False |
|Eigenaar_2 | UUID |  | False |
|Portefeuillehouder_1 | UUID |  | False |
|Portefeuillehouder_2 | UUID |  | False |
|Opdrachtgever | UUID |  | False |
|Titel | String |  | False |
|Inhoud | String |  | False |
|Weblink | String |  | False |
|Status | String |  | False |
|Volgnummer | String |  | False |
|Type | String | Geldig: ['Hoofdstuk', 'Afdeling', 'Paragraaf', 'Artikel', 'Lid'], | False |
|Gebied | UUID |  | False |
|Ref_Beleidskeuzes | Nested |  | False |

