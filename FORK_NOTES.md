# Fork provenance

This is a public derivative of
[`weicj/vLLM-2080Ti-Definitive`](https://github.com/weicj/vLLM-2080Ti-Definitive).

- Source commit: `93c9013e375b1ecbf2da88179d2a31175a0d5c99`
- Source commit title: `Merge pull request #245 from weicj/release/v0.2.2-post3`
- Source license: Apache-2.0; see the retained `LICENSE` file and notices.
- The source project is itself based on upstream vLLM, with the upstream
  baseline recorded in `README.md`.

This derivative preserves the original project identity and existing license
and copyright notices. Its change adds a configurable launcher limit for the
filesystem Disk KV cache and a periodic systemd cleaner. The cleaner only
removes `.bin` cache blocks; model weights, configuration files, and other
files are outside its eviction scope.
