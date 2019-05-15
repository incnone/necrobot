def kadgar_link(racer_1_name: str, racer_2_name: str) -> str:
    return '<http://{hostsite}/{r1name}/{r2name}>'.format(
                hostsite='kadgar.net/live',
                r1name=racer_1_name,
                r2name=racer_2_name
            )
