nd_emotes = {
    'cad': '<:cadence:676159524033527808>',
    'mel': '<:melody:676159691134337040>',
    'coh': '<:zelda:676158586975420457>',
    # 'coh': '<:NecroPuzzle:802722636832440330>',
    'noc': '<:nocturna:724439270047219713>',
    'dia': '<:diamond:798591449146327150>',
    'dor': '<:dorian:860614813456793630>',
    'suz': '<:suzu:1021133702991990824>',
    'eli': '<:eli:1021133703923122266>',
    'kla': '<:klarinetta:1021133705353363586>',
    'ari': '<:aria:1021133706506813540>'
}


def get_emote_str(league_tag):
    return '{} '.format(nd_emotes[league_tag]) if league_tag in nd_emotes else ''
