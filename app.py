#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🍟♤ ｐ𝓞т𝐀tᵒ 🐟🎁 Anime API
Combines AniList metadata + Consumet streaming.
Runs on Railway with a single exposed port.
"""
import os
import json
import time
import urllib.parse
import urllib.request
from flask import Flask, request, jsonify

# ---------- CONFIG ----------
CONSUMET_URL = os.environ.get("CONSUMET_URL", "http://127.0.0.1:3000")
PORT = int(os.environ.get("PORT", 8080))

app = Flask(__name__)

# ---------- HELPERS ----------
def http_get_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def http_post_json(url, payload, timeout=20):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

# ---------- ANILIST METADATA ----------
def fetch_anilist(query, per_page=10):
    gql = """
    query ($search: String, $perPage: Int) {
      Page(perPage: $perPage) {
        media(search: $search, type: ANIME) {
          id
          title { romaji english native }
          description(asHtml: false)
          coverImage { large extraLarge }
          bannerImage
          episodes
          duration
          genres
          averageScore
          status
          season
          seasonYear
          format
        }
      }
    }
    """
    data = http_post_json(
        "https://graphql.anilist.co",
        {"query": gql, "variables": {"search": query, "perPage": per_page}}
    )
    return data.get("data", {}).get("Page", {}).get("media", [])

# ---------- CONSUMET STREAMING ----------
def consumet(path):
    try:
        return http_get_json(f"{CONSUMET_URL}{path}")
    except Exception as e:
        return {"error": str(e)}

# ---------- ROUTES ----------
@app.route("/")
def home():
    return jsonify({
        "name": "🍟♤ ｐ𝓞т𝐀tᵒ 🐟🎁 Anime API",
        "status": "online",
        "endpoints": {
            "search": "/api/search?q=naruto",
            "providers": "/api/providers",
            "stream_search": "/api/stream/search?provider=gogoanime&title=naruto",
            "stream_episodes": "/api/stream/episodes?provider=gogoanime&id=naruto",
            "stream_watch": "/api/stream/watch?provider=gogoanime&episode_id=naruto-episode-1",
            "full": "/api/full?q=naruto&episode=1&provider=gogoanime"
        }
    })

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing ?q="}), 400
    try:
        results = fetch_anilist(q)
        return jsonify({"success": True, "count": len(results), "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/providers")
def api_providers():
    data = consumet("/anime")
    return jsonify(data)

@app.route("/api/stream/search")
def api_stream_search():
    provider = request.args.get("provider", "gogoanime")
    title = request.args.get("title", "").strip()
    if not title:
        return jsonify({"error": "Missing ?title="}), 400
    q = urllib.parse.quote(title)
    return jsonify(consumet(f"/anime/{provider}/{q}"))

@app.route("/api/stream/episodes")
def api_stream_episodes():
    provider = request.args.get("provider", "gogoanime")
    anime_id = request.args.get("id", "").strip()
    if not anime_id:
        return jsonify({"error": "Missing ?id="}), 400
    return jsonify(consumet(f"/anime/{provider}/info/{anime_id}"))

@app.route("/api/stream/watch")
def api_stream_watch():
    provider = request.args.get("provider", "gogoanime")
    episode_id = request.args.get("episode_id", "").strip()
    if not episode_id:
        return jsonify({"error": "Missing ?episode_id="}), 400
    return jsonify(consumet(f"/anime/{provider}/watch/{episode_id}"))

@app.route("/api/full")
def api_full():
    q = request.args.get("q", "").strip()
    episode = request.args.get("episode", "1")
    provider = request.args.get("provider", "gogoanime")
    if not q:
        return jsonify({"error": "Missing ?q="}), 400

    try:
        meta = fetch_anilist(q, per_page=1)
        meta = meta[0] if meta else None
    except Exception as e:
        meta = {"error": str(e)}

    stream_data = {}
    try:
        search = consumet(f"/anime/{provider}/{urllib.parse.quote(q)}")
        results = search.get("results", [])
        if results:
            anime_id = results[0].get("id")
            info = consumet(f"/anime/{provider}/info/{anime_id}")
            episodes = info.get("episodes", [])
            ep_id = None
            for ep in episodes:
                if str(ep.get("number")) == str(episode):
                    ep_id = ep.get("id")
                    break
            if not ep_id and episodes:
                ep_id = episodes[0].get("id")
            if ep_id:
                stream_data = consumet(f"/anime/{provider}/watch/{ep_id}")
    except Exception as e:
        stream_data = {"error": str(e)}

    return jsonify({"metadata": meta, "stream": stream_data})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": time.time()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
