from Dimensies.ambitie import Ambitie_Schema
from Dimensies.beleidsregel import BeleidsRegel_Schema
from Dimensies.doel import Doel_Schema
from Dimensies.provincialebelangen import ProvincialeBelangen_Schema
from Dimensies.beleidsrelaties import BeleidsRelatie_Schema
from Dimensies.maatregelen import Maatregelen_Schema
from Dimensies.themas import Themas_Schema
from Dimensies.opgaven import Opgaven_Schema
from Dimensies.verordening import Verordening_Schema

from Feiten.beleidsbeslissing import Beleidsbeslissingen_Meta_Schema, Beleidsbeslissingen_Fact_Schema, Beleidsbeslissingen_Read_Schema


dimensies = [
    {'schema': Ambitie_Schema, 'slug': 'ambities', 'tablename': 'Ambities', 'latest_tablename': 'Actuele_Ambities', 'singular': 'Ambitie', 'plural': 'Ambities'},
    {'schema': BeleidsRegel_Schema, 'slug': 'beleidsregels', 'tablename': 'Beleidsregels', 'latest_tablename': 'Actuele_Beleidsregels', 'singular': 'Beleidsregel', 'plural': 'Beleidsregels'},
    {'schema': Doel_Schema, 'slug': 'doelen', 'tablename': 'Doelen', 'latest_tablename': 'Actuele_Doelen', 'singular': 'Doel', 'plural': 'Doelen'},
    {'schema': ProvincialeBelangen_Schema, 'slug': 'provincialebelangen', 'tablename': 'ProvincialeBelangen',
        'latest_tablename': 'Actuele_ProvincialeBelangen', 'singular': 'Provinciaal Belang', 'plural': 'Provinciale Belangen'},
    {'schema': BeleidsRelatie_Schema, 'slug': 'beleidsrelaties', 'tablename': 'BeleidsRelaties', 'latest_tablename': 'Actuele_BeleidsRelaties', 'singular': 'Beleidsrelatie', 'plural': 'Beleidsrelaties'},
    {'schema': Maatregelen_Schema, 'slug': 'maatregelen', 'tablename': 'Maatregelen', 'latest_tablename': 'Actuele_Maatregelen', 'singular': 'Maatregel', 'plural': 'Maatregelen'},
    {'schema': Themas_Schema, 'slug': 'themas', 'tablename': 'Themas', 'latest_tablename': 'Actuele_Themas', 'singular': 'Thema', 'plural': "Thema's"},
    {'schema': Opgaven_Schema, 'slug': 'opgaven', 'tablename': 'Opgaven', 'latest_tablename': 'Actuele_Opgaven', 'singular': 'Opgave', 'plural': 'Opgaven'},
    {'schema': Verordening_Schema, 'slug': 'verordeningen', 'tablename': 'Verordeningen', 'latest_tablename': 'Actuele_Verordeningen', 'singular': 'Verordening', 'plural': 'Verordeningen'}
]

#  (schema_meta, schema_fact, schema_read , slug, tablename, actuele_tablename, singular, plural)
feiten = [
    {'meta_schema': Beleidsbeslissingen_Meta_Schema,
        'fact_schema': Beleidsbeslissingen_Fact_Schema,
        'read_schema': Beleidsbeslissingen_Read_Schema,
        'slug': 'beleidsbeslissingen',
        'meta_tablename': 'Beleidsbeslissingen',
        'meta_tablename_actueel': 'Actuele_Beleidsbeslissingen',
        'fact_tablename': 'Omgevingsbeleid',
        'singular': 'Ambitie',
        'plural': 'Ambities',
        'fact_to_meta_field': 'Beleidsbeslissing'}
]
