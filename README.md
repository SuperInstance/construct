# construct

Hardware-agnostic agent runtime with a layered trait system.

**Status:** Early stage — scaffolded, building, tests passing.

## What it does

Defines a trait-based runtime that agents implement to run on any target —
bare metal, OS, or wasm. Layers stack capabilities (logging, networking,
storage) so an agent picks only what it needs without coupling to a
specific platform.

## Building

```sh
cargo build
cargo test
```

## License

Licensed under either of [Apache License, Version 2.0](LICENSE-APACHE) or
[MIT license](LICENSE-MIT) at your option.
