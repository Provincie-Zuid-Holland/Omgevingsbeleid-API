def get_single_result(records):
    # try:
    print(records)
    assert(len(records) == 1)
    # except AssertionError as e:
    #     e.args += ("Meerdere resultaten gevonden, neem contact op met de systeembeheerder",)
    return records[0]
