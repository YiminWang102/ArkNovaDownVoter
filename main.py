from html.parser import HTMLParser
import requests
import time

# ELO THRESHOLD
ELO_THRESHOLD = 400

# True for Arena ranking, False for ELO ranking
## CURRENTLY DOES NOT WORK FOR ARENA RANKING, ONLY ELO RANKING
USE_ARENA_RANKING = False

# Rank range (0 - 4000 if arena ranking to cover elite and gold, or 0 - 8000 to cover silver and bronze too)
# (2000 - 30000 if elo ranking to cover 450 - 100 ELO)
START_RANK = 5000
END_RANK = 5010

# True if you want to un thumbs down people above the threshold 
UN_THUMBS_DOWN = False

# Delay in between 
DELAY = 0.01

# POPULATE COOKIES
cookies = {}

#### POPULATE HEADERS

# ELO RANKING HEADER - https://boardgamearena.com/gamepanel?game=arknova - ranking - All-time - Next>
ELO_RANKING_HEADERS = {}



#### IGNORE FOR NOW
# ARENA RANKING HEADERS - https://boardgamearena.com/halloffame?game=1741&season=19
ARENA_RANKING_HEADERS = {}

# ARK NOVA PLAYER ELO HEADERS - https://boardgamearena.com/playerstat?id=93599262&game=1741
ARK_ELO_HEADERS = {}


# Gets player ID and elos, sorted by ELO ranking
def fetch_ranking_elos(start):
    data = {
        'game': '1741',
        'start': start,
        'mode': 'elo',
    }

    headers = ELO_RANKING_HEADERS

    base_url = 'https://boardgamearena.com/gamepanel/gamepanel/getRanking.html'

    response = requests.post(base_url, cookies=cookies, headers=headers, data=data)
    data = response.json()
    ranks = data.get("data", {}).get("ranks", [])
    player_data = [(player["id"], player["ranking"]) for player in ranks]

    player_ids_and_elos = []
    for player_id, ranking in player_data:
        player_ids_and_elos.append((player_id, round(float(ranking) - 1300, 2)))

    return player_ids_and_elos


# gets player IDs sorted by arena ranking
def fetch_ranking_ids(start):
    params = {
        "game": 1741,
        "start": start,
        "mode": "arena",
        "season": 19,
        "dojo.preventCache": 1733522051571,
    }

    headers = ARENA_RANKING_HEADERS

    base_url = "https://boardgamearena.com/halloffame/halloffame/getRanking.html"

    response = requests.get(base_url, params=params, headers=headers, cookies=cookies)

    if response.status_code == 200:
        print("Request successful!")
        return get_player_ids_from_ranking_data_response(response)
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")
        return []


def get_player_ids_from_ranking_data_response(response):
    # Extract the list of ranks
    ranks = response.json().get('data', {}).get('ranks', [])

    # Extract player IDs
    player_ids = [player['id'] for player in ranks]

    return player_ids

class ELOParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.is_gamerank_value = False
        self.gamerank_value = None

    def handle_starttag(self, tag, attrs):
        # Check if the tag is a <span> with the class 'gamerank_value'
        if tag == "span":
            for attr_name, attr_value in attrs:
                if attr_name == "class" and attr_value == "gamerank_value":
                    self.is_gamerank_value = True

    def handle_data(self, data):
        # If inside a gamerank_value span, capture the data
        if self.is_gamerank_value:
            self.gamerank_value = int(data.strip())

    def handle_endtag(self, tag):
        # Reset the flag when the span ends
        if tag == "span":
            self.is_gamerank_value = False

eloParser = ELOParser()


def get_player_ark_nova_elo(player_id):
    headers = ARK_ELO_HEADERS

    params = {
        'id': player_id,
        'game': '1741',
    }

    base_url = 'https://boardgamearena.com/playerstat'

    print(f"getting player elo, id: {player_id}")
    response = requests.get(base_url, params=params, cookies=cookies, headers=headers)

    eloParser.feed(response.text)


def change_player_reputation(player_id, reputation):
    cookies = {
        'PHPSESSID': 'utdl1dp5555cq6r6vqujkdul3n',
        'TournoiEnLigne_sso_user': 'DugongEnjoyer%243%24ywang5991%40gmail.com',
        'TournoiEnLigne_sso_id': '546bd584e004f6aa9663b5df57b4622b',
        'TournoiEnLigneidt': 'm7mTz6TnY10qO4e',
        'TournoiEnLignetkt': 'hf5Qvgk9TJHGw9IuiNTH1YjleCIlpSA0Ycs2hpO0YbWJ3ACT6ax9QjRQf8HmnmeP',
        'TournoiEnLigneid': '8E3MnWfUDdGgvpk',
        'TournoiEnLignetk': '2gSArWUIuepL7sS2YtJSqkIfT7fyn0ySUMnHD4Z41DA4pbgr9vOM9PJpWjys57VH',
    }

    headers = ELO_RANKING_HEADERS

    params = {
        'player': player_id,
        'value': reputation,
        'category': 'personal',
        'dojo.preventCache': '1733523304772',
    }

    base_url = 'https://boardgamearena.com/table/table/changeReputation.html'

    print("changing player reputation", player_id, reputation)
    response = requests.get(base_url, params=params, headers=headers, cookies=cookies)
    if response.status_code == 200:
        print("Request successful!")
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")

def process_players_by_elo_rating():
    for start in range(START_RANK, END_RANK, 10):  
        time.sleep(DELAY)
        player_ids_and_elos = fetch_ranking_elos(start)
        if player_ids_and_elos:
            print(f"fetched players from rank {start + 1} to {start + 11}")
            for player_id, elo in player_ids_and_elos:
                print(f"player {player_id} has elo: {elo}")
                if elo < ELO_THRESHOLD:
                    print(f"player elo below threshold, thumbs down incoming")
                    change_player_reputation(player_id, -1)
                    time.sleep(DELAY)
                if elo >= ELO_THRESHOLD and UN_THUMBS_DOWN:
                    print(f"player elo above threshold, un thumbs down incoming")
                    change_player_reputation(player_id, 0)
                    time.sleep(DELAY)



def process_players_by_arena_rating():
    for start in range(START_RANK, END_RANK, 10):
        time.sleep(DELAY)
        player_ids = fetch_ranking_ids(start)
        print(player_ids)
        if player_ids:
            print(f"fetched players from rank {start + 1} to {start + 11}")
            print(player_ids)
            for player_id in player_ids:
                elo = get_player_ark_nova_elo(player_id)
                print(f"player {player_id} has elo: {elo}")
                
                if elo and elo < ELO_THRESHOLD:
                    print(f"player elo below threshold, thumbs down incoming")
                    change_player_reputation(player_id, -1)
                    time.sleep(DELAY)   
                if elo and elo >= ELO_THRESHOLD and UN_THUMBS_DOWN:
                    print(f"player elo above threshold, un thumbs down incoming")
                    change_player_reputation(player_id, 0)
                    time.sleep(DELAY)     


def main():
    if USE_ARENA_RANKING:
        process_players_by_arena_rating()
    else:
        process_players_by_elo_rating()

main()