# The Zdex dump format (schema version 1)

One JSON file per game build. Zircon writes it, any dumper can. This is the same text as https://zlogic.eu/zdex/format, kept here so it's easy to link and diff.

- A UTF-8 JSON object: a `header` (tool, source process, engine guess, engine offsets, globals) and a `packages[]` array.
- Every class, struct and enum has a **path** such as `/Script/Engine.Actor`. Paths are the identity; every cross-reference (super class, interfaces, member types, parameter types) is a path.
- Sizes and offsets are bytes. A property's `size` is its total size (element size × `array_dim`). Addresses are module-relative hex strings.
- Unknown keys are ignored, so a dumper can add its own fields. Missing optional keys are fine. Only the keys marked required are required.

## Top level

```json
{
  "schema_version": 1,
  "header": {
    "tool_version": "0.3.0",
    "created_utc": "2026-09-15T10:21:04Z",
    "source":  { "kind": "external", "process": "Game-Win64-Shipping.exe", "main_module": "Game-Win64-Shipping.exe",
                 "module_base": "0x7ff64be00000", "image_size": 171896832 },
    "engine":  { "version": "5.6", "confidence": 0.6, "evidence": ["version string: ++UE5+Release-5.6"] },
    "offsets": [ { "name": "UObject.ClassPrivate", "value": 16 }, … ],
    "globals": [ "GObjects=0x98670c0", "FNamePool=0x9783590" ]
  },
  "packages": [
    { "name": "/Script/Engine", "classes": [ … ], "structs": [ … ], "enums": [ … ] }
  ]
}
```

| Key | Required | Meaning |
|---|---|---|
| schema_version | yes | Integer, currently `1`. Zdex refuses other values. |
| header.tool_version | no | Free text naming the dumper and version. Shown on the dump page. |
| header.created_utc | no | ISO-8601 UTC timestamp of the dump. Becomes the build's "dumped" date. |
| header.source | no | `kind` is one of `internal`, `external`, `dump`, `static`; `process`, `main_module`, `module_base` (hex string), `image_size` (bytes). |
| header.engine | no | `version` such as `"5.6"`, `confidence` 0–1, `evidence[]` of human-readable strings. |
| header.offsets[] | no | Derived engine offsets `{name, value}`, for example `UObject.ClassPrivate`. Negative values mean "not found" and are dropped. |
| header.globals[] | no | Strings of the form `NAME=0xHEX`, module-relative. |
| names[] | no | Optional FName pool. Ignored on import. |
| packages[] | yes | Each with `name` (a package path) and optional `classes[]`, `structs[]`, `enums[]`. |

## Classes and structs

```json
{
  "name": "Actor", "path": "/Script/Engine.Actor", "cpp_prefix": "A",
  "super": "/Script/CoreUObject.Object",
  "size": 680, "alignment": 8, "inherited_size": 40, "vtable_rva": "0x7d655e8",
  "interfaces": [ "/Script/Engine.Interface_AssetUserData" ],
  "properties": [ … ], "functions": [ … ]
}
```

| Key | Required | Meaning |
|---|---|---|
| name, path | yes | Short name and the full object path. The path is the identity across the whole file and across builds. |
| cpp_prefix | no | `U`, `A`, `F`, `E`, `I`… Used to build the C++ name (`AActor`). Defaults by kind when missing. |
| super | no | Path of the parent class or struct. |
| size, alignment, inherited_size | no | Bytes. `inherited_size` is where this type's own members start (aligned). |
| vtable_rva | no | Classes only, hex string, module-relative. |
| interfaces[] | no | Paths of implemented interfaces. |
| properties[], functions[] | no | See below. |

## Properties

```json
{ "name": "bHidden", "type": { "kind": "bool", "raw": "BoolProperty", "size": 1 },
  "offset": 88, "size": 1, "is_bitfield": true, "bit_index": 7, "byte_mask": 128, "field_mask": 128,
  "flags": 545460846597, "flag_names": ["Edit", "BlueprintVisible", "Net"], "default": "false" }
```

| Key | Required | Meaning |
|---|---|---|
| name, type, size | yes | `type` is a type reference (below). `size` is the **total** size in bytes: element size × `array_dim`. |
| offset | no | Byte offset inside the owning type. Members without an offset are listed but not placed in the layout. |
| array_dim | no | Static array element count, only when greater than 1. |
| is_bitfield, bit_index, byte_mask, field_mask | no | For `bool` bitfields sharing one byte. |
| flags, flag_names[] | no | Raw EPropertyFlags as an integer and the decoded names. |
| default | no | Default value as a string, taken from the class default object. |

## Type references

Recursive. `kind` is one of `bool int8 uint8 int16 uint16 int32 uint32 int64 uint64 float double string name text struct enum objectptr classptr weakptr softptr softclassptr lazyptr interface fieldpath delegate multicast_delegate array set map optional unknown`. `raw` is the engine's property class name (`StructProperty`). `name` is the referenced path for struct/enum/object kinds. `params[]` holds inner types: `array` and `set` have one, `map` has key and value, `enum` may carry its underlying integer type.

```json
{ "kind": "map", "raw": "MapProperty", "size": 80,
  "params": [ { "kind": "name", "raw": "NameProperty", "size": 8 },
              { "kind": "struct", "raw": "StructProperty", "size": 24, "name": "/Script/CoreUObject.Vector" } ] }
```

## Functions and parameters

```json
{ "name": "SetActorHiddenInGame", "flags": 1409286144, "flag_names": ["Final", "Native", "Public", "BlueprintCallable"],
  "native_rva": "0x1b2c4f0",
  "params": [ { "name": "bNewHidden", "type": { "kind": "bool", "raw": "BoolProperty", "size": 1 }, "size": 1, "offset": 0 } ],
  "script": [ { "offset": 0, "text": "…" } ], "script_size": 42, "script_complete": true }
```

| Key | Required | Meaning |
|---|---|---|
| name | yes | Function name inside its class. |
| native_rva | no | Hex string, module-relative address of the native implementation. |
| flags, flag_names[] | no | EFunctionFlags raw and decoded. |
| params[] | no | Each with `name`, `type`, `size`, optional `offset`, `is_out`, `is_const`, `is_return`. There is no separate return field: the parameter with `is_return: true` is the return value. |
| script[], script_size, script_complete | no | Decompiled Blueprint bytecode as `{offset, text}` lines; `script_complete: false` when decoding stopped early. |

## Enums

```json
{ "name": "ENetRole", "path": "/Script/Engine.ENetRole", "underlying": "uint8",
  "values": [ { "name": "ENetRole::ROLE_None", "value": 0 }, { "name": "ENetRole::ROLE_Authority", "value": 3 } ] }
```

`underlying` defaults to `uint8`. Values wider than the underlying type are widened on import; negative values in unsigned enums are wrapped.

## Rules of thumb for other dumpers

- Emit paths exactly as the engine reports them (`GetPathName()`); Zdex diffs builds by path.
- Sizes are bytes, offsets are bytes, addresses are hex strings relative to `module_base`.
- Leave out what you do not know rather than guessing; every key except the ones marked required is optional.
- Gzip the file before uploading. The first 64 KB must contain `"schema_version"` and `"header"` — write the header first.
- Test with the API: `POST /upload/init` → chunks → `finish`; a rejected file comes back with a message naming what is missing.

Something in the format holding you back? Say so through " rel="noopener">the contact form; the schema grows by adding keys, never by breaking existing ones.
