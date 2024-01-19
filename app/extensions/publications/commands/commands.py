import uuid
from typing import Optional

import click
from sqlalchemy import select, text
from app.core.db.session import SessionLocal

from app.core.dependencies import db_in_context_manager, depends_db
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.publications.dso.dso_service import DSOService
from app.extensions.publications.models import (
    PublicationBill,
    PublicationPackage,
    PublicationConfig,
)
from app.extensions.publications.repository.publication_repository import PublicationRepository


@click.command()
def test_dso_call():
    """
    Insert in package create endpoint 
    """
    with SessionLocal() as db:
        click.echo("STARTED TEST")
        test_package = uuid.UUID("233161e076f54f7db8a9b026d386a300")
        test_bill = uuid.UUID("f6dd58c2ab7843fea3fed37e08634a04")

        # Step 1: Fetch required data from database
        pub_repo = PublicationRepository(db)
        bill_db = pub_repo.get_publication_bill(uuid=test_bill)
        package_db = pub_repo.get_publication_package(uuid=test_package)
        config_db = pub_repo.get_latest_config()

        bill = PublicationBill.from_orm(bill_db)
        package = PublicationPackage.from_orm(package_db)
        config = PublicationConfig.from_orm(config_db)

        # Step 2: Call DSO Service dummy data for now
        service = DSOService(db)
        input_data = service.prepare_input_data(bill, package, config)
        service.build_dso_package(input_data)

        # Step 3: TAKE STATE AND BUILD EXPORT FORMAT
        # state_exported = service.export_state()

        # Step 4: Store results in database + OW Objects
        # ow_repo = OWObjectRepository(db)
        # pub_repo.create_ow_object()
