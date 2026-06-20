# Easter eggs & neofetch

E-Console hides a few treats. They're discoverable on purpose — run `eggs` in
UNISHELL to list them, like `man fortune`. Everything here works in both the
native TUI (`python3 -m econsole`) and the [browser preview](../index.html).

## neofetch — and adjusting it

`neofetch` (alias `fetch`) prints an E-Console logo beside your system info.

```sh
neofetch                 # print the fetch into UNISHELL
neofetch --logo pi       # one-off logo override (econsole | ascii | blocks | pi)
neofetch --no-colors     # drop the colour-block row
neofetch config          # open the interactive, adjustable neofetch app
```

In the **neofetch app** press `o` (or click *configure*) to toggle the config
view, then:

- **↑↓** select an option, **space** toggle it
- **←→** cycle the logo (`auto`, `econsole`, `ascii`, `blocks`, `pi`)
- toggle the **colour blocks** row
- toggle any **field** on/off (OS, Host, Kernel, Uptime, Shell, Resolution,
  Profile, Theme, Panes, Apps, Commands, Packages, CPU, Memory, Python, Firewall)
- **r** reset to defaults

Changes are saved immediately to the `neofetch` section of
`~/.config/econsole/config.json`, so your fetch looks the way you like it every
time. The logo defaults to `auto`, which uses the plain-ASCII logo under
high-contrast/E-Ink themes and the boxed Unicode logo otherwise.

## The egg catalogue

| Trigger | What happens |
|---|---|
| `eggs` / `eastereggs` | Lists these eggs (with a wink) |
| `sl` | A steam locomotive chuffs by — you meant `ls`, didn't you? |
| `cowsay <text>` | An ASCII cow says your text (wraps nicely) |
| `fortune` | A random terminal/E-Ink fortune |
| `coffee` / `tea` / `brew` | `HTTP 418 — I'm a teapot.` ☕ |
| `xyzzy` | "Nothing happens." (Colossal Cave Adventure) |
| `sudo <cmd>` | Permission theatrics — try `sudo make me a sandwich` (xkcd 149) |
| `matrix` | "Wake up, Neo…" and flips you to the green `matrix` theme |
| `theme apply rainbow` | Applies the **secret** 🌈 theme (hidden from `theme list`) |
| `calc 6*7` | Certain results get a comment — `42`, `1337`, `69`… |
| **Konami code** | In the browser preview: `↑ ↑ ↓ ↓ ← → ← → B A` unlocks the rainbow theme |

## Why discoverable?

Hidden-but-findable is friendlier than truly secret: the `rainbow` theme is
appliable yet omitted from listings, and `eggs` documents the rest — the same
spirit as classic UNIX `fortune`/`sl`. None of them touch your data or the
system; they're pure fun built on the same command + theme plumbing as the rest
of the shell.
