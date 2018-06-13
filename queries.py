"""
Query file voor alle endpoints. 
"""

# Queries voor thema

# Een thema selecteren op `id`. (Beschikbare argumenten `:id` van gevraagde thema)
thema_op_id = 'SELECT * FROM themas WHERE id=:id'

# Alle thema's selecteren.
alle_themas = 'SELECT * FROM themas'

# Alle opgaven die bij een thema horen selecteren. (Beschikbare argumenten `:id` van gevraagde thema)
alle_opgaven_bij_thema = 'SELECT * FROM opgaven WHERE thema=:id'

# Opgaven

# Een opgave selecteren op `id`. (Beschikbare argumenten `:id` van gevraagde opgave) 
opgave_op_id = 'SELECT * FROM opgaven WHERE id=:id'

# Alle opgaven selecteren
alle_opgaven = 'SELECT * FROM opgaven'

# Alle thema's die bij een opgave horen selecteren. (Beschikbare argumenten `:id` van gerelateerd thema)
alle_themas_bij_opgave = 'SELECT * FROM themas WHERE id=:id'

# Alle ambities selecteren
alle_ambities = 'SELECT * FROM ambities'