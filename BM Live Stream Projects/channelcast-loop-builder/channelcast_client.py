"""
Minimal client for the ChannelCast MCP HTTP endpoint.

The server (ASP.NET, https://channelcast.tv/mcp) speaks MCP over HTTP and
answers each POST independently -- no session handshake required. Every reply
comes back as a one-line Server-Sent-Events body ("data: {json}"), so we just
POST JSON-RPC and parse the single data line out.
"""

import json
import requests


class ChannelcastError(RuntimeError):
    pass


class ChannelcastClient:
    def __init__(self, base_url: str, token: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._id = 0

    # -- low level -----------------------------------------------------------
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

    def _rpc(self, method: str, params: dict):
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        resp = requests.post(self.base_url, headers=self._headers(),
                             json=payload, timeout=self.timeout)
        if resp.status_code != 200:
            raise ChannelcastError(f"HTTP {resp.status_code}: {resp.text[:300]}")

        # Body is text/event-stream: find the 'data:' line(s) and take the last
        # one that parses to a JSON-RPC envelope.
        result = None
        for line in resp.text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                line = line[5:].strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "error" in obj:
                raise ChannelcastError(str(obj["error"]))
            if "result" in obj:
                result = obj["result"]
        if result is None:
            raise ChannelcastError(f"No result parsed from response: {resp.text[:300]}")
        return result

    # -- tools ---------------------------------------------------------------
    def call_tool(self, name: str, arguments: dict = None):
        """Call an MCP tool and return its parsed JSON payload (tools return
        their data as a JSON string inside content[0].text)."""
        result = self._rpc("tools/call", {"name": name, "arguments": arguments or {}})
        content = result.get("content", [])
        for c in content:
            if c.get("type") == "text":
                txt = c.get("text", "")
                try:
                    return json.loads(txt)
                except json.JSONDecodeError:
                    return {"text": txt}
        return result

    # -- convenience wrappers -----------------------------------------------
    def list_channels(self):
        return self.call_tool("list_channels")

    def list_playlists(self, channel_id):
        return self.call_tool("list_playlists", {"channelId": channel_id})

    def list_playlist_items(self, playlist_id):
        return self.call_tool("list_playlist_items", {"playlistId": playlist_id})

    def list_media(self, search=None):
        return self.call_tool("list_media", {"search": search})

    def list_categories(self, channel_id):
        return self.call_tool("list_categories", {"channelId": channel_id})

    def add_media(self, title, provider_url, description=None):
        return self.call_tool("add_media", {
            "title": title, "providerUrl": provider_url,
            "description": description,
        })

    def add_media_to_playlist(self, playlist_id, media_id):
        return self.call_tool("add_media_to_playlist", {
            "playlistId": playlist_id, "mediaId": media_id,
        })

    def remove_playlist_item(self, playlist_item_id):
        return self.call_tool("remove_playlist_item", {"playlistItemId": playlist_item_id})

    def reorder_playlist(self, playlist_id, ordered_media_ids):
        return self.call_tool("reorder_playlist", {
            "playlistId": playlist_id, "orderedMediaIds": ordered_media_ids,
        })

    def update_playlist(self, playlist_id, name=None, description=None, gap_seconds=None):
        return self.call_tool("update_playlist", {
            "playlistId": playlist_id, "name": name,
            "description": description, "gapSeconds": gap_seconds,
        })

    def delete_playlist(self, playlist_id):
        return self.call_tool("delete_playlist", {"playlistId": playlist_id})
