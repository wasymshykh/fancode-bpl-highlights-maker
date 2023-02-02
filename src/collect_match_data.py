"""

    Collects match highlight data from fancode.com's graphql routes and stores it to data/matches.json file.

"""

import requests
import json
import time

headers = {
    'Accept': 'application/json',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'source': 'fc-web'
}

def get_matches_request ():
    page_no = 1
    has_next_page = True
    matches = []

    while has_next_page:
        r = requests.get('https://www.fancode.com/graphql?operationName=GallerySection&operation=query&variables={"filter":{"collectionId":2159425,"segmentId":18431,"contentDataType":"DEFAULT"},"page":'+str(page_no)+'}&extensions={"persistedQuery":{"version":1,"sha256Hash":"91acca9e733735eb207e1f8c5e31a949cf73fe3138f36fbcd5a2214f7d6b394b"}}', headers=headers)
        print("REQ-1 - PAGE - " + str(page_no) + " : " + str(r.status_code))

        if r.status_code == 200:

            _response = r.json()

            if _response["data"] is not None:
                if _response["data"]["contentSegment"] is not None: 
                    if _response["data"]["contentSegment"]["edges"] is not None:

                        if (_response["data"]["contentSegment"]["pageInfo"]["next"] is None):
                            has_next_page = False
                        else:
                            page_no = _response["data"]["contentSegment"]["pageInfo"]["next"]

                        for _match in _response["data"]["contentSegment"]["edges"]:
                            url = _match['mediaSource']['native']
                            if (url.startswith("https://vod-gcp")):
                                url = url.replace("https://vod-gcp.", "https://")
                                url = url[:url.index("_logo_added")+11] + ".mp4"

                            _new_match = {
                                "matchId": _match['matchId'],
                                "mediaSource": url,
                            }
                            matches.append(_new_match)

                    else:
                        has_next_page = False
                        print("[edges] is not found in body")
                else:
                    has_next_page = False
                    print("[contentSegment] is not found in body")
            else:
                has_next_page = False
                print("[data] is not found in body")
        else:
            has_next_page = False
            print("Request is failed.")

        time.sleep(3)
    
    return matches

def get_match_content (matchId):
    _payload = {
        "operationName":"MatchDetails",
        "operation":"query",
        "variables":{"matchId":matchId,"isLoggedIn":False},
        "query":"query MatchDetails($matchId: Int!, $isLoggedIn: Boolean!) { match: matchWithScores(id: $matchId) { streamAuthorization { authorizationType } isUserEntitled ...MatchDetailsFragment } fantasyLinks(matchId: $matchId) { ...fantasyLinks }}fragment fantasyLinks on FantasyLinksSection { title subTitle segments { id title subTitle type }}fragment MatchDetailsFragment on Match { id teamType sport { name slug collectionSlug } name tour { collectionId name id logo { src } collectionSlug } status startTime streamingStatus isPremium isUserEntitled @include(if: $isLoggedIn) streamAuthorization { authorizationType } squads { flag { src } name color shortName isWinner cricketScore { runs overs balls status wickets } kabaddiScore { points onFieldPlayers totalFieldPlayers raiding } footballScore { points } basketBallScore { points } status { cricket { isBatting } } } format isScorecardAvailable isLiveStreamingAvailable venue articleCount scorecard { cricketScore { description } kabaddiScore { description matchClock } footballScore { description matchClock } basketballScore { description matchClock } } videoId: videoStreamId matchDesc city winner { shortName name } mediaId notificationStatus { enabledTypes { notificationId notificationName } } notifications { supportedTypes { notificationId } } bucketId}"
    }
    res = requests.post("https://www.fancode.com/graphql", json=_payload, headers=headers)
    
    _body = res.json()

    matchDetails = {}
    if (_body["data"] is not None):
        if (_body["data"]["match"] is not None):
            _match = _body["data"]["match"]
            matchDetails["shortName"] = _match["name"]
            matchDetails["venue"] = _match["venue"]
            matchDetails["matchNo"] = _match["matchDesc"]
            matchDetails["matchResult"] = _match["scorecard"]["cricketScore"]["description"]
            matchDetails["teamOne"] = _match["squads"][0]["name"]
            matchDetails["teamTwo"] = _match["squads"][1]["name"]

    return matchDetails

matches = get_matches_request()
i = 0
for _match in matches:
    print("GETTING_MATCH_DETAILS...")
    try:
        content = get_match_content(_match['matchId'])
        print("SUCCESS_MATCH_DETAILS")
        matches[i]['content'] = content
    except:
        print("ERROR_MATCH_DETAILS!!!")
    i += 1
    time.sleep(3)

# saving json to file
f = open("data/matches.json", "w")
f.write(json.dumps(matches))
f.close()
