# Zdex

Public index of Unreal Engine reflection dumps.

https://zlogic.eu/zdex/

Pick a game, pick a build, browse the whole type system with real offsets. Search it, diff two builds, download the usmap or a C++ SDK. Basically what dumpspace does, but the way I wanted it to work.

I make [Zircon](https://zlogic.eu/zircon/), the dumper that feeds it. `zircon dump --pid <pid> -o game.json --publish` and the build is online a minute later. Any other dumper works too as long as it writes the same JSON (see below).

## What's on the site

- Browser: packages on the left, types in the middle, detail on the right. Memory layout strip, bitfields with bit index and mask, inherited members if you want them, functions with param offsets and native RVAs, Blueprint bytecode when the dump has it.
- Search over type / member / function / enum value names. CamelCase aware, so `walk speed` finds `MaxWalkSpeed`. Per dump or across everything.
- Diff between two builds of the same game. Added/removed types, members that moved or changed type, function signatures, engine offsets. Useful after a patch.
- Per dump: `.usmap` (v3, works in FModel/CUE4Parse), a header-only C++ SDK that compiles under MSVC with a `static_assert(sizeof)` per type, and the original JSON.
- JSON API for all of it, plus a chunked resumable upload with API keys.

No tracking, no third-party requests, no ads.

## Uploading

Make an account (Discord or email), drop the JSON on the upload page, done. Or make an API key on your account page and let Zircon upload for you:

```
zircon login
zircon dump --pid <pid> -o game.json --publish
```

Uploads get reviewed before they go public. Reflection metadata only, never game files. What you upload is on you, terms are at https://zlogic.eu/zdex/terms.

## The format

Zdex reads one JSON file per game build, `schema_version` 1. Zircon writes it, but it's not tied to Zircon in any way. It's documented in [FORMAT.md](FORMAT.md) (same content as https://zlogic.eu/zdex/format). If your dumper can produce it, it can publish.

## API

Reads are public, uploads need a bearer key.

```
curl -s -A "mytool/1.0" "https://zlogic.eu/zdex/api/v1/dump/3/type?path=AActor"
```

Upload is `POST /upload/init` -> `POST /upload/chunk` (x n) -> `POST /upload/finish` -> poll `GET /dump/{id}/status`. Full reference at https://zlogic.eu/zdex/developers. Send a real User-Agent, Cloudflare drops the default library ones.

[examples/publish.py](examples/publish.py) is a small reference client, stdlib only.

## This repo

The site itself is a PHP app and isn't published here. This repo is for the format spec, the example client, and issues. For anything else use the contact form at https://zsync.eu/ttz/.

Related: [Zircon](https://zlogic.eu/zircon/), [zlogic.eu/mods](https://zlogic.eu/mods/), [zsync.eu](https://zsync.eu/).
