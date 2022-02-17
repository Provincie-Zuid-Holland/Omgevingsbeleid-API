# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2022 - 2022 Provincie Zuid-Holland


from flask.helpers import get_debug_flag
from dotenv import load_dotenv

from Api.application import create_app
from Api.settings import DevConfig, ProdConfig

# @note: we probably still need load_dotenv for our acc/prod deploys?
load_dotenv()

CONFIG = DevConfig if get_debug_flag() else ProdConfig

app = create_app(CONFIG)
