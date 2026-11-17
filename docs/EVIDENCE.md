# On-chain evidence

Every row below was read off the two chains by `scripts/collect-evidence.py`, which writes this file and `agent/ledger/chain-events.jsonl` from the same pass. Nothing here is typed by hand.

* **Enforcer (Reactive Lasna, 5318007)** — `0xf24f1d13F995a2368015868048F791426AfeD39C`
* **Vault (Base Sepolia, 84532)** — `0x9ED8FAD6627B89104b5a5C2C31334168Ce73EB77`
* **Cycles seen:** 158 · **full cycles:** 144
* **Proposals clamped by the contract:** 143
* **Proposals stopped by the economic veto:** 113
* **Proposals rejected before execution:** 1
* **Rebalances that moved funds:** 4 (of which 2 opened a liquidity position)
* **Autonomous exits (contract acted without the model):** 1
* **No-trades (move below the minimum trade):** 140

## The loop, leg by leg

A full cycle has six legs. The first three are the Reactive part: the contract opens the cycle on Lasna, calls back to the vault on Base Sepolia, and the agent answers by posting a proposal. The last three are the enforcement part: the contract judges the proposal against the envelope, and either moves the position or refuses to.

| Cycle | Opened (Lasna) | Asked (Base) | Posted (Base) | Judged (Lasna) | Result | Model → enforced | Clamp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [`0x838960…`](https://lasna.reactscan.net/tx/0x8389609044c23d05dfd4c9ee3e94a1dd2d8cf128d0ba192508bbc40b67cde089) | [`0xedb550…`](https://sepolia.basescan.org/tx/0xedb5507a8dc60a559397e4617f6804b37b0ee4e9cc58166c1a1d12f7423efc3c) | [`0x900015…`](https://sepolia.basescan.org/tx/0x9000153cff80d1d8d52263bfaffd42660c4657244d9f5ca779c0ee4d604a5b29) | [`0xdfa515…`](https://lasna.reactscan.net/tx/0xdfa5152aaac0e6c654ca358c6eba1866757ea3ce5e8361e12b7bce3d7018b651) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 2 | [`0x01a2ab…`](https://lasna.reactscan.net/tx/0x01a2ab43f717831ff4a2b9d5092210d83e4cdfed9b4e206f0245c0be7a948c34) | [`0x01de5b…`](https://sepolia.basescan.org/tx/0x01de5b2b05cc5d4ce7baf896340c08462a0ff3c27d024aac62897eadce9476d5) | [`0x465a48…`](https://sepolia.basescan.org/tx/0x465a48e0fde71a2fafff5fdada8785ec42b4ce9129ab7ab169aae67d484dd980) | [`0xebd2fb…`](https://lasna.reactscan.net/tx/0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070) | rebalanced | 7102 → 4000 bps | LP_ABOVE_MAX |
| 3 | [`0xdd906e…`](https://lasna.reactscan.net/tx/0xdd906e0099a1c04fa1eedd2e1509c4732fa910464ef4bf0dff0b8051ac7eed67) | [`0xc6c22c…`](https://sepolia.basescan.org/tx/0xc6c22c51b755c1041b499290d984f4561206c454418fd9593680d60ade911f41) | [`0x78ac45…`](https://sepolia.basescan.org/tx/0x78ac45223b61d2df05bf66822b4cb3876541a0313987c4fab3896325b0d56b38) | [`0xe5095b…`](https://lasna.reactscan.net/tx/0xe5095bf7ba8fc77afe15208c72b4a22734b002bf6ccf3ab66a96398595887121) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 4 | [`0x0f3011…`](https://lasna.reactscan.net/tx/0x0f3011b01b04086e807f08aae69913cb3f6fb80a6450806ac97d2037e232d65d) | [`0x48e96b…`](https://sepolia.basescan.org/tx/0x48e96b95651b205c33e5a35671a4d7e36d26f33333a19a41f8becb0912c93bd4) | [`0x3fdb7a…`](https://sepolia.basescan.org/tx/0x3fdb7a21af31a7bdb23ba6776f3cbee4e46e95dd5fde98adba30b37198825f40) | [`0xad7c59…`](https://lasna.reactscan.net/tx/0xad7c59d88e7c046cbe629ad350537d8da1854437d51a38c6c8f2b0ac7b4a86b9) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 5 | [`0x7c585d…`](https://lasna.reactscan.net/tx/0x7c585d89604141944322b385baf78b172dadd32bbcca79757603f840be72c73f) | [`0xa3382e…`](https://sepolia.basescan.org/tx/0xa3382ecea191cfb43f0e784ad9fb0f51cdc2b1ac3e2d1aef583681adbb0de45f) | [`0x91586b…`](https://sepolia.basescan.org/tx/0x91586b018684c8bf6258bc724da6f1a1ffff4f85635c4a45e20b0b85ac962f3d) | [`0xf8078c…`](https://lasna.reactscan.net/tx/0xf8078cebbf85185091b015728feaef7ad723da03dfdb698cc3110fb34f524d59) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 6 | [`0x2858ef…`](https://lasna.reactscan.net/tx/0x2858ef8165d436c0dfbee8a25aab921db82ac66b11dcf041feea109e8b030451) | [`0xda8eb3…`](https://sepolia.basescan.org/tx/0xda8eb3d48eb7d3fec87113ba9b84388576c947f8779ffa6e1a940e02447fe174) | [`0xfbbbbe…`](https://sepolia.basescan.org/tx/0xfbbbbe20c88f0ef2c4b8e35ea43b5721d7c50b7cf3effc0cfd92f786a01e2740) | [`0xa96ac7…`](https://lasna.reactscan.net/tx/0xa96ac77fdfa95cf907a31ffc6c25458b5828e423ced711790140ba05bd4c22fe) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 7 | [`0xcc48db…`](https://lasna.reactscan.net/tx/0xcc48db98513d7c84fbf0b52ac4a498ff2d43b52416dd7a6750950cfa8b6dc6e2) | [`0x832474…`](https://sepolia.basescan.org/tx/0x832474cf4398555d1fbb47a0ddc3c315b7b1a7714ccf1ecdda70d0d978e883e1) | [`0x053c7f…`](https://sepolia.basescan.org/tx/0x053c7f1a75edc7e6aa53cf6f67f69bea79c760ca1542ef6c0d865300d275c988) | [`0x01a585…`](https://lasna.reactscan.net/tx/0x01a5856e731e104ba490893a883fab5712896c19bb57efb20c5e90ee90ad4c0d) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 8 | [`0xc13c72…`](https://lasna.reactscan.net/tx/0xc13c7238ce95b80aa719b506883d12ed38544f254ac98c1d58b22d0ec9e4a9b3) | [`0xf7496c…`](https://sepolia.basescan.org/tx/0xf7496c0b744c3a3ccfebcb341360d6f90c611a87a32a57637bc0dd1c92a3d4de) | [`0xce42ce…`](https://sepolia.basescan.org/tx/0xce42ce6403a1b1e0321baf7589461b2109a142e7491141731fe433e047f9cce8) | [`0xe48045…`](https://lasna.reactscan.net/tx/0xe48045872db488e0a5e69ba62bba82c48c52d35873e4aa2dbf8fde3f44bf5c94) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 9 | [`0xa82eab…`](https://lasna.reactscan.net/tx/0xa82eab3f0b064e53a8db7012b1564b8bd0ea5e84c7783d165d44de00489a4834) | [`0xe8d13e…`](https://sepolia.basescan.org/tx/0xe8d13e1d9b1856ca53cd107e56663655c50371c71aa8f040eddec1c7cdf51e39) | [`0xe283b3…`](https://sepolia.basescan.org/tx/0xe283b3880634f2bf4d0e0394f07b77f6453548a7e09cd9fa9cefa57148762579) | [`0x4b56e9…`](https://lasna.reactscan.net/tx/0x4b56e9bed865264e93255c3f7476e08739bbc519b2ac1ef390e77435ca843f7e) | rejected | 7102 → — bps | CYCLE_MISMATCH |
| 13 | [`0x717966…`](https://lasna.reactscan.net/tx/0x7179665d346fc0daf87b8f43d659f7fc8dfb06c6412f1eccff51fcf9a2a33296) | [`0x9d158c…`](https://sepolia.basescan.org/tx/0x9d158c84f144fdea206b5913c014e19137118c6b578b705fa13de7a0ee3771f2) | [`0x58da1b…`](https://sepolia.basescan.org/tx/0x58da1bf95d8bd7d1d37b2bc53b3629f82a5e8afd53cfab3f086dea379c3371e2) | [`0x544fe3…`](https://lasna.reactscan.net/tx/0x544fe3c634e9e32c5a3d6b480e03a90944f2ac82c41f43e4b48dcd68d0bebc71) | rebalanced | 7102 → 4000 bps | LP_ABOVE_MAX |
| 14 | [`0x2b373f…`](https://lasna.reactscan.net/tx/0x2b373f427a630ce00950a5a336ed683e315f213668db8cafa23fe13f3a23eb37) | [`0xbb2926…`](https://sepolia.basescan.org/tx/0xbb2926598f2dae68fd22fe4a5c8330fb40cdb1ca5af78bb44fac895edf7b2620) | [`0xd060a4…`](https://sepolia.basescan.org/tx/0xd060a4deffe3ec24d65638eb6d27e5b36a0d2be233b19e566928cd690c2f9d5b) | [`0x237e17…`](https://lasna.reactscan.net/tx/0x237e172aad28e7dc7286d0bb05f81d3425b7b449fa5656633dc6b3fc1f593fca) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 15 | [`0x0a60a9…`](https://lasna.reactscan.net/tx/0x0a60a9bf20841d4be0a4f3474ca30b05f003f4418be4eeb634cbe3a5ade97b17) | [`0x05daf3…`](https://sepolia.basescan.org/tx/0x05daf3cc08a24f6fc0990bd0007ee7e51db9ae51c027fc3b5c0b98291ff38fda) | [`0x820564…`](https://sepolia.basescan.org/tx/0x82056494d57bea079b74da750b3baa0751ebc7d7fce24eeac5de3c3d59c6de9f) | [`0xdfd54c…`](https://lasna.reactscan.net/tx/0xdfd54c6825796c7297d057af2500fc3a593545494c8482adc762c52bd62def18) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 16 | [`0xf05e7e…`](https://lasna.reactscan.net/tx/0xf05e7ebac34d0566429b55c923aa4859d285cf5976136b84a022e9692b9077dc) | [`0xc78a48…`](https://sepolia.basescan.org/tx/0xc78a48bdc4b671ade7918f45670576ad91943de3a29959b32813f520f0aab91d) | [`0x0cbf21…`](https://sepolia.basescan.org/tx/0x0cbf21d7d296bd2c49227748bf3c2d2145602a5546f85cafc599989c7a275d25) | [`0x38997d…`](https://lasna.reactscan.net/tx/0x38997d63e281a6d18b913a45075d85ec87a4e48940163b6060ddba48b5a7f0de) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 17 | [`0xf307f5…`](https://lasna.reactscan.net/tx/0xf307f534ac323bca9c1a8bf5b8d175d7fefe6dca198317342fc336e05f7ea7ce) | [`0x4e5917…`](https://sepolia.basescan.org/tx/0x4e591772a7ff4846312f463a8dee7d450c1401fc6513249b9248e48e309684fa) | [`0xb4aef1…`](https://sepolia.basescan.org/tx/0xb4aef1066b9c89680a5e43f4cef1321cb44c7a7ebdc747f78e9483d933ea543d) | [`0x0d32b8…`](https://lasna.reactscan.net/tx/0x0d32b81a7e97d1780d5d828e8a1d2388c57586b11be5d87bb86b1277cd073951) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 18 | [`0xbe72b7…`](https://lasna.reactscan.net/tx/0xbe72b700e47816865a935d0fbf842019b2d2de44d8ad151fd41ad5943909df56) | [`0x488257…`](https://sepolia.basescan.org/tx/0x488257fa01baef580202525d806e5eb46ee7836601729848053b4f937e6cf398) | [`0x291885…`](https://sepolia.basescan.org/tx/0x2918857ae85f9593e65776f808443a5e2b0dae9d409d77824de75bc7eb12fa02) | [`0x98b0be…`](https://lasna.reactscan.net/tx/0x98b0bee7e0342d31b33e2c6e464dc3e4968168e1070e214b26d3303544434290) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 19 | [`0x48de69…`](https://lasna.reactscan.net/tx/0x48de69ca6bb263bab7671538427a4b68a89a5a9ff32f89488bc42087c9ff8fc4) | [`0x397153…`](https://sepolia.basescan.org/tx/0x3971532dc9080b67ced7a16209ccefc981d1532b51d9465ecb444b9a54fc6e65) | [`0xcf2edc…`](https://sepolia.basescan.org/tx/0xcf2edcf151deb709140002e8ed7d37b23eb088ee4a83c8e4567650eba925d76c) | [`0x58acf3…`](https://lasna.reactscan.net/tx/0x58acf326434024c9f4f9029d96d5eef80b851f7427f2fe1ec306fea1f75af882) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 20 | [`0x5b09c5…`](https://lasna.reactscan.net/tx/0x5b09c51244f1b0fbd4a3995a8540d6efb8a8ffd855ca45e0f99d0aa4d8722a0b) | [`0x17b5a3…`](https://sepolia.basescan.org/tx/0x17b5a31a27b143f3e6cf6c260d84d3e96f1505b347312a1656b973f22d3b85f3) | [`0x351b5e…`](https://sepolia.basescan.org/tx/0x351b5e1cebe0e3a12b3ef6b42623856a78e8ab9859599458ef36369ed32f306b) | [`0x6fa4ac…`](https://lasna.reactscan.net/tx/0x6fa4ac4a9ff929d6d831fa3ed384a9c53f18c20226c5bb9d1b0d4ba18f757aad) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 21 | [`0x2cf4f1…`](https://lasna.reactscan.net/tx/0x2cf4f10de921f8d585fd250798d2f64ee8ad4651bee2143b9684380d1e64d324) | [`0x518b41…`](https://sepolia.basescan.org/tx/0x518b419da1cd6f7a7d7fda1c339adaf0b3bf3bfa96bbb7e96aec5a3a320dbdfe) | [`0xf7f6db…`](https://sepolia.basescan.org/tx/0xf7f6db352d05400bb52aee9430fbc8955a449d7e357355171d1c521a5252fd11) | [`0xc9177b…`](https://lasna.reactscan.net/tx/0xc9177bd479c5d22bf9150c63e12f026a0c756cc1d638716e6fc769ee77a09492) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 22 | [`0x789305…`](https://lasna.reactscan.net/tx/0x789305c5110c7deda4f62e37e5afac171028ad484c0215515aad34b733f44e27) | [`0x7e4f2b…`](https://sepolia.basescan.org/tx/0x7e4f2b08f96604eddf7ec3def229fc2c6269869a8fc3a346662e0f5a667612c7) | [`0xd6092f…`](https://sepolia.basescan.org/tx/0xd6092f07398d5c49610caea28267f5b1ad921bfa0e54a40bedef942bc19a9bd0) | [`0x75188f…`](https://lasna.reactscan.net/tx/0x75188f5de6aa432b30d8e0b18a5bfa301ca58c243d5b009c2991ebaf1ffd0be3) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 23 | [`0x32e796…`](https://lasna.reactscan.net/tx/0x32e796c2f2c1390b2cfb11ed06679d4e28a2fcc20cef5f7b9be180a3143ea230) | [`0x7b9325…`](https://sepolia.basescan.org/tx/0x7b93256773ffedf681e60ce67a4f6185b68f47b37f81da439d8c4f71bda1ba3a) | [`0x9df282…`](https://sepolia.basescan.org/tx/0x9df282798bd166b96c29fc1db7d59111825bcb03b7fcdc42213a308e7f7e694d) | [`0x2735b5…`](https://lasna.reactscan.net/tx/0x2735b593f3b126a311d814f8ed8b12c10680aa77029c4683daa0885b0f9b19c6) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 24 | [`0xe3c0fe…`](https://lasna.reactscan.net/tx/0xe3c0febacea9893274e2ffaf12675256b952c7f26e41bd3d9fb669b66a6ea302) | [`0xcc8112…`](https://sepolia.basescan.org/tx/0xcc8112832eaa936c9439e2ae4e134f0d379f8ce94557a2021336be40c9b7db5d) | [`0xc5dce1…`](https://sepolia.basescan.org/tx/0xc5dce1d99e3d03ad4c7d19d504da3aa2982757840753d9297139f1636141c264) | [`0xac771e…`](https://lasna.reactscan.net/tx/0xac771ea54e9f17c3d4589db616c7097683d4a5f0f8803fd7a1b2fe335f58dc2f) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 26 | [`0x5d56bf…`](https://lasna.reactscan.net/tx/0x5d56bf9dae8ff90e10b390390bea564309996df7ffa007998fde048c8e98fe62) | [`0x464910…`](https://sepolia.basescan.org/tx/0x464910eeb06eff810a62bb2dd3b72912b943cd4132f3853404a8077b627cd88b) | [`0x490c74…`](https://sepolia.basescan.org/tx/0x490c7401e1795758ec1df4604fe787381c2cd076fcc3ade204ae6e202812b6e6) | [`0x012e5b…`](https://lasna.reactscan.net/tx/0x012e5b4995d6ff17967e32fb56e007cea7c09ac45135bcb4dace2d5505368522) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 27 | [`0x03388c…`](https://lasna.reactscan.net/tx/0x03388c596780925fb31d1610cde42663af28cd944721606a650cc9a36e7fae65) | [`0xbcd6fe…`](https://sepolia.basescan.org/tx/0xbcd6fe6f819560105837f2a25a3ea5e73cb8787a273ecc73aaab7a390c75a666) | [`0x84ccae…`](https://sepolia.basescan.org/tx/0x84ccaea95c2c167e4ef5a1427184c50ae04b570a8c7a973cde14535734829e37) | [`0x64d0d5…`](https://lasna.reactscan.net/tx/0x64d0d557cf9046e8946eab50a9fc7ea7ff1097d46a04151800696196e3bc56c8) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 28 | [`0xc76c5c…`](https://lasna.reactscan.net/tx/0xc76c5c7bbd43a34172db584173f8d267506ec04aea4ae7db1a6fad8257ff559d) | [`0x57174e…`](https://sepolia.basescan.org/tx/0x57174e99d1bb1492dbe4bab6a2b9b935142dd91b61421dbd5e3ecc300995925c) | [`0xc7ff5e…`](https://sepolia.basescan.org/tx/0xc7ff5e227802d7ecb5353c1f91499edf7a89ba61451e79a772323651ce65a740) | [`0xdcea31…`](https://lasna.reactscan.net/tx/0xdcea313f8d571d5555760d9146391c3bae209246ddba198e86d1d2ae6db9ee86) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 29 | [`0xc12b8b…`](https://lasna.reactscan.net/tx/0xc12b8b38419c39ff9455b2a8b3beb5758b363aa21b8f4c34c6ef878dbda3e3e4) | [`0xa5ef36…`](https://sepolia.basescan.org/tx/0xa5ef368e26f85e8ba955f4a5ba3eca69cb4d6f6cefc7e47042fd21b3d13dcffb) | [`0xe12f6d…`](https://sepolia.basescan.org/tx/0xe12f6de898f9ffe69f7c900853cf792d80c8e15f6a8aef0c766043de04de3ce8) | [`0x92b4d5…`](https://lasna.reactscan.net/tx/0x92b4d5252776e5f395a760a46090a847b254f70658711b03bd01dd0ce3670eb0) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 30 | [`0x7a0ef6…`](https://lasna.reactscan.net/tx/0x7a0ef62e3f8304c3c54aaf58c25dd0b733e87eeaeff7878c000f959e26e7875d) | [`0xa16b1c…`](https://sepolia.basescan.org/tx/0xa16b1cb62bf4b881d58f538e16d01040b0af6815a581638a4768344cef859b2a) | [`0xc046fa…`](https://sepolia.basescan.org/tx/0xc046fa60db2089768d612fdd8f1cb86dcd7d343a115fa283781240981015db25) | [`0x7aa574…`](https://lasna.reactscan.net/tx/0x7aa5745e9b69591f6e17a4c32aada5af52a6b6451f6fe2a4d6d4675714783b18) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 31 | [`0x964b8f…`](https://lasna.reactscan.net/tx/0x964b8f8a23d25afd291f2b257a7b8f991ad1fa7e40995a970ef1218bf0e8e5cf) | [`0x6ec7b6…`](https://sepolia.basescan.org/tx/0x6ec7b66be2f03ab62d374fa2be283a691a409fb7f27fe8aa8789a15a320a3725) | [`0x1bb40f…`](https://sepolia.basescan.org/tx/0x1bb40fddbfbe7ae02c155e925dd2dd986b5ef95b36dc017c78f4f0c3edbbe205) | [`0x454f2a…`](https://lasna.reactscan.net/tx/0x454f2a55c2439ddfc0bafa70e4dae80ef46d60e0219d51cc5ef1cbc91dc50433) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 32 | [`0x8fdc6b…`](https://lasna.reactscan.net/tx/0x8fdc6b76c12c56a0b071273f537c39fbdedbc30e47dd81d49116f44ea21a55a9) | [`0xda4a23…`](https://sepolia.basescan.org/tx/0xda4a234e8dcf0ec3fabc21e671128d6115a2bedae291f19902611fe41d788ace) | [`0x7eae08…`](https://sepolia.basescan.org/tx/0x7eae081cdc1fd85115475f74ff859bee3f2ade361876406435cfc05389a6f987) | [`0xd6d2c6…`](https://lasna.reactscan.net/tx/0xd6d2c6540d23ef1a3ff421d950c22123071a00af8a30bb3c53e655fbc611243c) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 33 | [`0x76e9bc…`](https://lasna.reactscan.net/tx/0x76e9bc96b400de8d053bd314ad4269bb42cc53b15cba0c7612fbf8973720a3b8) | [`0xa62be5…`](https://sepolia.basescan.org/tx/0xa62be50e7887c04bf027af1883433112230dc49bd43ffaf062b289b9bce8f406) | [`0x795922…`](https://sepolia.basescan.org/tx/0x795922bcc5d022c5ea5f5cfb0a220246c6e03577349fa68febcf7713081ffd8d) | [`0x0e344d…`](https://lasna.reactscan.net/tx/0x0e344da0efa75d5fc87f0bc1e51fd7b622a3f4206827c9e66018abaf4fa355f9) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 34 | [`0x26180c…`](https://lasna.reactscan.net/tx/0x26180c64bad7a2ba6ddeeca34680dcdb183df23443b4e23940c5aba7cd3f5efe) | [`0x1c3ff0…`](https://sepolia.basescan.org/tx/0x1c3ff068a6249693420d17e16bf141d9c5793c345dddab9ddc31cfe9bcc02c94) | [`0xa1d4ac…`](https://sepolia.basescan.org/tx/0xa1d4ac8bbaa0d5bd4859c99e04a75b5fb84953b1dc27a8c4851cc215404e8195) | [`0x6f424a…`](https://lasna.reactscan.net/tx/0x6f424ad21fd34e83d9e83f4753052b9f0457b2f51ed8a7cda69a5e938fe27d0e) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 35 | [`0xebac9b…`](https://lasna.reactscan.net/tx/0xebac9b1281ba776c77a5a80a6215b929303fea4f6fcf218116e302c4e50223c2) | [`0xb5bd47…`](https://sepolia.basescan.org/tx/0xb5bd472307175635d9482ab2acabb1994fbffae31e30a03ccd943c1fa86636e1) | [`0xe7bea2…`](https://sepolia.basescan.org/tx/0xe7bea283303b826ecc87405bacf209ee8d144daa81c2ad03078b2f8e4ab233f0) | [`0x6e623b…`](https://lasna.reactscan.net/tx/0x6e623b1b8266d5169681677d8dc1c0820e30dd91bfe9350fc7f354965602fc1c) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 36 | [`0x6b0876…`](https://lasna.reactscan.net/tx/0x6b087644f0b6c8de038e4f9a548ca189f1d70842f8d3da89b6dabafe9809aaa7) | [`0x59e801…`](https://sepolia.basescan.org/tx/0x59e80169e7d02b7f23029b4ca7c156cdbbd83747cb51be7009a7a95ecfe2c8fe) | [`0xf651a0…`](https://sepolia.basescan.org/tx/0xf651a09c92d94c85fed4a2411444bcd427d12efaa6a8702f8fb5f5e45752e9a0) | [`0xbf0077…`](https://lasna.reactscan.net/tx/0xbf0077bb6f5f9b4cdd9308fa693bdfe9baa21822bc905bde5afec637bed69c3f) | no_trade | 7102 → 4000 bps | LP_ABOVE_MAX |
| 37 | [`0xd546d4…`](https://lasna.reactscan.net/tx/0xd546d45568977025a7bd60e6695871f923e3a1a33623559354babfb2832c3908) | [`0x889d09…`](https://sepolia.basescan.org/tx/0x889d0946911861b7f53fcb29144b4a982fa1264ddf3cabae45488a9c632a33ba) | [`0x13fe39…`](https://sepolia.basescan.org/tx/0x13fe3944decb8580753b90934be077e946b6de775e3a9b1218d29b7ee52d9d3f) | [`0x0d2845…`](https://lasna.reactscan.net/tx/0x0d2845aa3c3dd6e30863c29f836871d72e65813bc4974d741893a949912d6e58) | rebalanced | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 38 | [`0x42aa67…`](https://lasna.reactscan.net/tx/0x42aa676d6d375f6a3a6adb723ca2bd15a8d87ea4e6f227dc837c061689c3ba94) | [`0x0f6fa6…`](https://sepolia.basescan.org/tx/0x0f6fa6c8c25083c9e1ddab6a5c6f53123cfd37eca61391ddb70b92f9ad85e576) | [`0x9c7104…`](https://sepolia.basescan.org/tx/0x9c710488ebfd4618f1e45cd1db8caaab76f895700efbcfecd6e46d4f1557a3f1) | [`0xec82a5…`](https://lasna.reactscan.net/tx/0xec82a50ce78152d420e8008389dac8823011550569f7cd16c53a57c66701a013) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 39 | [`0x15c8d9…`](https://lasna.reactscan.net/tx/0x15c8d9091ed4cb6f67b0a3af884c62261f219f596dafccb17ae2f4cd55d0009b) | [`0x2e2309…`](https://sepolia.basescan.org/tx/0x2e23090803c1c1d48f0312fa1c6040d5987b06dde832f77be5d023ccface9d58) | [`0xb28e92…`](https://sepolia.basescan.org/tx/0xb28e9224e243cf2a17c996f905e6d5e96cb67d4a48927c56eb3459e8e23ade60) | [`0xf716dc…`](https://lasna.reactscan.net/tx/0xf716dcfe11ec2e5994af522a1987246f61dc989d48b9faab3c514ebb5f54e8f1) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 40 | [`0x40032b…`](https://lasna.reactscan.net/tx/0x40032b38bffecbcdb1fc289cb6ec245c37e43b11ac0614b44f71108b60412938) | [`0xdeef42…`](https://sepolia.basescan.org/tx/0xdeef422406b9a28aa5837f718aa63b3cb37810b82f0219c01f2e004ed79c76d9) | [`0xd58c67…`](https://sepolia.basescan.org/tx/0xd58c6770b0d525922bf5553746ffe266d4664db0ee85bf699a7cf400e70f3b68) | [`0x0cb25b…`](https://lasna.reactscan.net/tx/0x0cb25b833db2479b5d44d64dc15cc7dae5a3e8b427c7cc69fe4bde46ec52baf2) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 41 | [`0xdcaa40…`](https://lasna.reactscan.net/tx/0xdcaa408d14e97d0357753af93a7825af5f22b719c7ab973a8c1783055d569f0c) | [`0xa59097…`](https://sepolia.basescan.org/tx/0xa59097fcc34228f86776e58389bae6f017d63c522081cf17cf9476fec3a51ab2) | [`0xb88bc5…`](https://sepolia.basescan.org/tx/0xb88bc55174ff7d63074f0bd1c9f5564d2c96b9bd362834ffa77854c5c37b2bdf) | [`0xbccd17…`](https://lasna.reactscan.net/tx/0xbccd17ec7217be26d8199a7403fa7436bc75371377acaec0c916a8b782beb95c) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 42 | [`0x140e83…`](https://lasna.reactscan.net/tx/0x140e836f7ee48e31ce621e1810e4c07bb05fad9d474047b8024c9b6cfd309043) | [`0xe5a67d…`](https://sepolia.basescan.org/tx/0xe5a67dce3c7f27d04037147938e7f0b266757d7279870338f37b76babac4c7b8) | [`0x47022d…`](https://sepolia.basescan.org/tx/0x47022d947f1b57dcc755073f923ed874d6240295ead01ff8e3e8008423055f7c) | [`0x3fa495…`](https://lasna.reactscan.net/tx/0x3fa495a597f912b8c37bb975b6d380d900f7be40592003d6b145119ee2b495b8) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 43 | [`0x262286…`](https://lasna.reactscan.net/tx/0x2622861beb89b468b7401f90fca9c5a29567989fa1a7e8628d7877a8929a8050) | [`0x2e0d78…`](https://sepolia.basescan.org/tx/0x2e0d78adb31bba39b2dca1db0fdda825ee4976909ef8313cee1e8500a27d77be) | [`0x1f31bd…`](https://sepolia.basescan.org/tx/0x1f31bd5395722730fd53f528c3dc42e4dfaa2d6e56cdf3484814668987df2425) | [`0x5be31e…`](https://lasna.reactscan.net/tx/0x5be31e0a330b53ecdb4072466051ace2e3bb042f02b3da5ca7712f43941792e7) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 44 | [`0x1fb730…`](https://lasna.reactscan.net/tx/0x1fb730bb9b5eac45ab4d97e1971739f5878844728ce818dc1d4a7d430a6c96d7) | [`0xb79d6f…`](https://sepolia.basescan.org/tx/0xb79d6f810e50ffee285fcb718b824d16ab7f6fd16df98a891ae4ca416de7053a) | [`0xc5e726…`](https://sepolia.basescan.org/tx/0xc5e726e97344662cbc42c8bd4b55a81c8cbea5e9a82b882cc2d54645e018b8d5) | [`0x9b3b34…`](https://lasna.reactscan.net/tx/0x9b3b34829156d00968175adac88455ed3be50bdec28455b963284879615412b1) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 45 | [`0x853603…`](https://lasna.reactscan.net/tx/0x853603c04a46e950638ca9780a59931418cefb864602c007a94c0eed0ac5ab33) | [`0xb89ff4…`](https://sepolia.basescan.org/tx/0xb89ff4aa66c27a4a3203d765c1699138d9f7a8f35183dda83b18edfc53a42b69) | [`0xcd678d…`](https://sepolia.basescan.org/tx/0xcd678d82537f720d8edaf6906042c26f9dde0af3865b9f81eb7e7ebf34755520) | [`0xcaf7af…`](https://lasna.reactscan.net/tx/0xcaf7afbdd893a8f98d83af9756e93eef411e76ae061dbd3ba007fd94caafa9be) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 46 | [`0x0a8b33…`](https://lasna.reactscan.net/tx/0x0a8b33ff22843ec3c0cae099a2b3ba15c8da9ab0eb81c441847ba883740d1630) | [`0xb581b8…`](https://sepolia.basescan.org/tx/0xb581b828bfa36e2ad48994bfdaac80cb42432fce2eef6bb0463264adcaf2e6a1) | [`0x4d0741…`](https://sepolia.basescan.org/tx/0x4d0741d48188812abd3041d47668cecead22e612c7e427ca72560dbe2010583d) | [`0x6fe235…`](https://lasna.reactscan.net/tx/0x6fe2352b78b332c81b728604a6c7bb312c7f0cd0625daf84500568762e1448fb) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 47 | [`0x27d3d7…`](https://lasna.reactscan.net/tx/0x27d3d7d2a4e7a49c82137d74206d5675015f23c3804c38178e7a924295f64190) | [`0x9767a6…`](https://sepolia.basescan.org/tx/0x9767a6d4dbdfe375e30f57f4606d49cd162881f659e408197457c71653aa6124) | [`0x319195…`](https://sepolia.basescan.org/tx/0x3191957613b23135fc2d184caa77d27ed5241c4aaffc98a77f182a4a77f8f722) | [`0x1843b7…`](https://lasna.reactscan.net/tx/0x1843b72918002b2c08d7b7be239b6ebd0264563262fca06fabb47318d45e4959) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 48 | [`0x014260…`](https://lasna.reactscan.net/tx/0x014260404a1f0623bcebbd68eda88d4f52ef91b48a85d4f425ca1dfe765a12c3) | [`0xbbb998…`](https://sepolia.basescan.org/tx/0xbbb9980d4d10954a27a13cf3ec9818510b957a7863c2e1b22981c822ffb3e631) | [`0x54c3d1…`](https://sepolia.basescan.org/tx/0x54c3d165c058b38a59cb4e1863423fdef2250718a0bd276dfff4d4f9c84563a6) | [`0x54e3ba…`](https://lasna.reactscan.net/tx/0x54e3ba38092a3ed58ee080d915853e2212ba8e11fff15c095f70a5c08624f21d) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 49 | [`0x7dbe7c…`](https://lasna.reactscan.net/tx/0x7dbe7c2e1bbf90c6f85366ce5affe8369d91987f3b6c5c0031ac65439c525710) | [`0xfda12e…`](https://sepolia.basescan.org/tx/0xfda12e4f064b376cca8dc1a60b4a74627338f2d5b7518fce98052b00c4bab368) | [`0x4734ba…`](https://sepolia.basescan.org/tx/0x4734baf5655947c4984c96557189d0add103bd0591931d0706bbe9a07cbc48d3) | [`0xcdec5d…`](https://lasna.reactscan.net/tx/0xcdec5de88b4405f6a86f5564facdae4f41c1be8e0ee9f4d26741f936c0f322d9) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 50 | [`0x3adc4f…`](https://lasna.reactscan.net/tx/0x3adc4fa577726e2f80885f08ae8c8aaacac1ddadda8e8721cd76f11301b28be9) | [`0x404556…`](https://sepolia.basescan.org/tx/0x40455676f0bf61dd1a74b8f1749d0ee417a962ef1c043a10da695ecf5457d51d) | [`0x4f66f5…`](https://sepolia.basescan.org/tx/0x4f66f5493e020b0017615aeaee928293244aa56559258e1c98e0a42f07f7eec6) | [`0x864b86…`](https://lasna.reactscan.net/tx/0x864b867625fe9db65e16e084adf06c00dde5ee8a31ecdeaa71451f61a9a7a633) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 51 | [`0x01aa93…`](https://lasna.reactscan.net/tx/0x01aa93183f678db7b245f48e6a1e3eea73f4cc048028891a5900ece85f04ab32) | [`0xcfad1c…`](https://sepolia.basescan.org/tx/0xcfad1cc47679add21b8094be17e79a36b00e50d08f8c82b03dce4c102457418b) | [`0xa36382…`](https://sepolia.basescan.org/tx/0xa3638285baf68b217e38b07ba511a1c6801f99e170c1ac82733204834de865ac) | [`0x5b6957…`](https://lasna.reactscan.net/tx/0x5b6957bd36e1114d9d0873c785a366dcf998e2d49081dd0cd18ad67b946807f3) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 52 | [`0x497e07…`](https://lasna.reactscan.net/tx/0x497e07061f62c1c40a23d95e16bb48f6b920e6ae2104c0599732e47c2755da2e) | [`0xd2bd5b…`](https://sepolia.basescan.org/tx/0xd2bd5b405ff76c101196836c4cce6c395763d1f4afd6a6ddfea6398a7c57147c) | [`0x0ab2c7…`](https://sepolia.basescan.org/tx/0x0ab2c7be9408cf4f0469c4266e32aaba129e94228444589c277ecfb195a0fa4e) | [`0xbe156a…`](https://lasna.reactscan.net/tx/0xbe156a86bb14cb5bd856fb52f08fe86c3001316214d4e5d0238aa819047a89d6) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 53 | [`0x89375e…`](https://lasna.reactscan.net/tx/0x89375e99f088f236c4b61cb01d12155c2e73231073627bdaba5d656b03b5ae9a) | [`0x22b023…`](https://sepolia.basescan.org/tx/0x22b0236b515f1ff1f1383ea8828a93d17ccff51be3ba1cd92dca9c24bbe6428e) | [`0x5ad739…`](https://sepolia.basescan.org/tx/0x5ad739dbbdd70f35238bda1d947e82bf6dd3fbff942ff85053d6958fe77d25e8) | [`0x42fb26…`](https://lasna.reactscan.net/tx/0x42fb26a9a666ae4b9d7d0e4070ee767d88afecadb61f636ffd47bc252ac7cf23) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 54 | [`0xf12904…`](https://lasna.reactscan.net/tx/0xf1290499eccf3f96431f97557071edbe2bea7aeadf31e5ea81617ae84d307594) | [`0x744c4a…`](https://sepolia.basescan.org/tx/0x744c4aba642492229c5d86b528e261a3f78bbb31aed7e7c0ae6a063161c6a9fc) | [`0x305b9f…`](https://sepolia.basescan.org/tx/0x305b9ff5a16285a93dcbee8c0ad38ef033f294a9f03b74b7fab7adc3a15bb9c1) | [`0x86f31f…`](https://lasna.reactscan.net/tx/0x86f31f42298cbd013d17cc035cc9da44d852e9a21a8caf39a8a512527e319c01) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 55 | [`0x6931d6…`](https://lasna.reactscan.net/tx/0x6931d689554396ddf7c1018a32bd5844bd1c33eeb5f564b0ef7e50cb62492b0a) | [`0x74087a…`](https://sepolia.basescan.org/tx/0x74087a0a67b05440dd416449b31df13a32298c83d612cf35b4fd2da535a95647) | [`0x418cab…`](https://sepolia.basescan.org/tx/0x418cabddd1de297c6f506f271942dc5ceac851add3ad97bbbb8ed2af30b22861) | [`0x5ff59f…`](https://lasna.reactscan.net/tx/0x5ff59f0b48f9ca499fcaf373aad9f0ac60c8455e8aff66cd98dff9679958b399) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 56 | [`0x824f80…`](https://lasna.reactscan.net/tx/0x824f803cbdcf26f153451a31ac5e4e191799b89879ebbfc3efc0e09114c4b714) | [`0xf54cac…`](https://sepolia.basescan.org/tx/0xf54caca9fbbf1b443d37901966c9d5dd38742d233d8fa4f7eb247d3501736201) | [`0xcedc3c…`](https://sepolia.basescan.org/tx/0xcedc3cba6eef4cb122556d15c874c58c40a9e747c3565c1c7dfce9f8ba0d87b7) | [`0xb37d26…`](https://lasna.reactscan.net/tx/0xb37d2639439df06a704ef6e8adf2f2c6ccd75fec7e6bfc0973561526c0cc373a) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 57 | [`0x377a43…`](https://lasna.reactscan.net/tx/0x377a43d85b85fe1eaa022efc2f6fde92582753ea4b4b5ae29b7ae691bbc21e99) | [`0x1f7ba9…`](https://sepolia.basescan.org/tx/0x1f7ba94ebe3d8e8f8a3a90dc64b389490cb6736d00027aaf5480ed57751d2dbb) | [`0x3deefb…`](https://sepolia.basescan.org/tx/0x3deefbb4b5e0afd5b50d788f451591e5ae7dcca10d2acf023366b447d6643dc1) | [`0xe5015c…`](https://lasna.reactscan.net/tx/0xe5015ccf58985599fac6e073f15eb451acbb00bb6ec536ca71d2053eb260d0e9) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 58 | [`0xd8478f…`](https://lasna.reactscan.net/tx/0xd8478fc1bd70437dc01639e2b3fdc5c2deed96ae4cd9ca292dd7d174ec06f372) | [`0x3586d5…`](https://sepolia.basescan.org/tx/0x3586d50dc0e969fcbd035e2a6c6e0fffd7ce1cb6fc7df4bd1de350508471ea0d) | [`0x4f7e30…`](https://sepolia.basescan.org/tx/0x4f7e308c12e4cc627261901a40d586498484d4d34358dc22f4a9779abefaf8c2) | [`0xcdd349…`](https://lasna.reactscan.net/tx/0xcdd349fe4eb94ef6f5f04db7ec3f4788ab90749f3020509b26372c50211ecfea) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 59 | [`0xd77259…`](https://lasna.reactscan.net/tx/0xd77259b7ca8c9f1bbcecba37e567727d20a765f9f3fa87a24f30cddf7947a548) | [`0x81148b…`](https://sepolia.basescan.org/tx/0x81148b3a2aa935c2f35f52fd97062b7c5264194a7dc8488ebd3d9723723d1054) | [`0x326ef8…`](https://sepolia.basescan.org/tx/0x326ef8800c4c3304090ad21ef34ba687710c4b56c42aa8e3eaa33029cfdbd696) | [`0x91a039…`](https://lasna.reactscan.net/tx/0x91a03911052be26ac821764735e02622249c7504d6e42341369b10a6650d2cfa) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 60 | [`0xf85879…`](https://lasna.reactscan.net/tx/0xf85879fc89b55e1000b2cb775542064de088bc1614af0ecf37407280387f0107) | [`0x6cbc01…`](https://sepolia.basescan.org/tx/0x6cbc019cae3430c88fdc4fdbb9d93924c568edac444227a6715e2523eb442351) | [`0x24de7e…`](https://sepolia.basescan.org/tx/0x24de7e9c83342e93976764720466b0a69cae33951dceaf8fb621b00787c5960b) | [`0x4672bc…`](https://lasna.reactscan.net/tx/0x4672bc4da578a85b45855c041c3a5c11e0a64c3ca8e57ca56e9de37f9eae4e5f) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 61 | [`0x63171a…`](https://lasna.reactscan.net/tx/0x63171ac4824edace8e2497b2b8ed17c3304ec608aa5ec174cd9f633345f40b9e) | [`0x15ca41…`](https://sepolia.basescan.org/tx/0x15ca4138a224f4fdad9f422deaf7fbce2fc41b595f3526aea8480bfa2f16535e) | [`0xa4b91f…`](https://sepolia.basescan.org/tx/0xa4b91f6381e0d8d8db6fed7c29e85c82b9c876ccaa08a45dd42353e4cc65a696) | [`0x76c052…`](https://lasna.reactscan.net/tx/0x76c052dcc11eccfda620e1358a15caa1e8ebecd15ab6e931172fa129befd6cf2) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 62 | [`0xb8d532…`](https://lasna.reactscan.net/tx/0xb8d532e4b3cc9b5610714872fee1d058c28e3e940b146273ec41a9b3ce8d9bab) | [`0x515d37…`](https://sepolia.basescan.org/tx/0x515d37c3d82ce79034410b9bfb6fa53cf75d95ee98ef055f717ca7ba19130212) | [`0x447866…`](https://sepolia.basescan.org/tx/0x44786669df8b47c974b01073343d9797a8cc27d5ca8cd7fbecb2fa04ab4586e4) | [`0x1989cd…`](https://lasna.reactscan.net/tx/0x1989cd93aa099157f2f07e602dc3399a01c131ff161d9a9685eaa84681a76159) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 63 | [`0x9d63d4…`](https://lasna.reactscan.net/tx/0x9d63d497c168f090ec9990ea4fba0322905afc75154ede595c2c4876de4f0a24) | [`0xc2faba…`](https://sepolia.basescan.org/tx/0xc2faba85f984eda93abae936c32aaddae78031fed866aa43c68b863753dd8820) | [`0xb3f477…`](https://sepolia.basescan.org/tx/0xb3f477e90ef7133668fc001d5a820f99ae6a8e7d0723fa0fcdac34186731359c) | [`0x12c7b8…`](https://lasna.reactscan.net/tx/0x12c7b898efea0c3fc41820b0887c2f7c37e02c75180d0cde9c18039e996869b2) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 64 | [`0x455b46…`](https://lasna.reactscan.net/tx/0x455b46363838de0025ef6a882de9d4def80f5c8e068e956bc9ec9a04eda0bf4c) | [`0x6c9b0a…`](https://sepolia.basescan.org/tx/0x6c9b0ae68dc1a49bb971a0b32b86fc4b84984e9eb7ae40f0a8a6e11f0a96f27f) | [`0xe06365…`](https://sepolia.basescan.org/tx/0xe06365bd0357f946f5b3946ae3d288d0a310b9228847b77d71ad2b0467ab65ee) | [`0x20b11c…`](https://lasna.reactscan.net/tx/0x20b11c63578ebb0efe17c0e690b2ca29afea75171348540fb6509f3b75cd0c9d) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 65 | [`0x94642d…`](https://lasna.reactscan.net/tx/0x94642d44f63bfd395f5f037326562bb24cfdbd32c8e1dce83cf6ca756eb48be7) | [`0xda41a0…`](https://sepolia.basescan.org/tx/0xda41a0a7bf27432fbfc26a885ac43c66753042760fc26d540317119dc970fc24) | [`0x89ee85…`](https://sepolia.basescan.org/tx/0x89ee858fe8ca397ce914659e46408431ec29a8214f4cb0bc33abe2d8946778b4) | [`0x5430ab…`](https://lasna.reactscan.net/tx/0x5430ab79ae2692d8b11bf8020f287fb8246dbf6041d7fe1276b98d4eb7a7333c) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 76 | [`0x6aa2e6…`](https://lasna.reactscan.net/tx/0x6aa2e6e5bbc03eef50a5869bb3c08e30f704ab646de0907970e3a725ed2f6bd4) | [`0xf5b2db…`](https://sepolia.basescan.org/tx/0xf5b2dbf4efbefa0785b3d1074bd5a1624eb5a0c2aef8dd0e9d792378d7d94f08) | [`0xd80d1a…`](https://sepolia.basescan.org/tx/0xd80d1a745c65406d090446fbee18e92fc53a03dd9a8ee9adffc3a168a0290f2a) | [`0x5c9d97…`](https://lasna.reactscan.net/tx/0x5c9d97a141c59b8754d5c0bb333a7c8e2cbd7c3afda045a172a6ea40067715aa) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 77 | [`0xcd74d0…`](https://lasna.reactscan.net/tx/0xcd74d059a102c7278d2c5427660cfa384c459e82b308a774fd3d1950edc812bb) | [`0xe8af46…`](https://sepolia.basescan.org/tx/0xe8af460b5b718d653d6ae47a7b9afce8beee4abe91d065abd63eded44f0b1e6a) | [`0xb0c408…`](https://sepolia.basescan.org/tx/0xb0c408903fea9576a4d226301435f1b3c5f50507e3794b0f1ae47d0571e53299) | [`0x96b0b5…`](https://lasna.reactscan.net/tx/0x96b0b5545136a909d7e6c427a4c8589388b80d5c5cc14ac912747f85ac5463a5) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 78 | [`0xc92a92…`](https://lasna.reactscan.net/tx/0xc92a9280d96ac34433378ca0015517a7aa26ad5b6b155f7d774dfe30f8d4a172) | [`0xfae645…`](https://sepolia.basescan.org/tx/0xfae645dbf6877fbdf50bebcaf6654020ca830f01069c3d203f09bc289d41da61) | [`0xe72e65…`](https://sepolia.basescan.org/tx/0xe72e652822ee95ca379df2be4f83ac4347d68738b49760c6874d3666f36e363a) | [`0xab8fde…`](https://lasna.reactscan.net/tx/0xab8fde9b6f6bf94630ae89e45f96c069bfea588a9389ea1d5422d61991885910) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 79 | [`0xd9e5d2…`](https://lasna.reactscan.net/tx/0xd9e5d2fc01457e17c97ee6d361e5f58cfdb1e15a086575fa8298247a7ef8141c) | [`0x1ca91f…`](https://sepolia.basescan.org/tx/0x1ca91f85dd6705ed8b46d63ca9217f5a763171905b3d81a33b2c54b0efa95e43) | [`0x596f27…`](https://sepolia.basescan.org/tx/0x596f272ef996b1f4f265cc3900c13ffb00d878b6e2520971d0a637075b9144a8) | [`0xf61525…`](https://lasna.reactscan.net/tx/0xf6152559d27e1110d5be28bc672748ffcbbb4e2534790db2c30247f7564b09f3) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 80 | [`0x7c53ca…`](https://lasna.reactscan.net/tx/0x7c53ca680104e43a610dd4a652d7614231b8add4fbf443fe166ec8f380a43180) | [`0xff6d3f…`](https://sepolia.basescan.org/tx/0xff6d3f8b7d53140f865db38c2565f09cee599bd1cb37562f35c635bf25840c0a) | [`0x8174f8…`](https://sepolia.basescan.org/tx/0x8174f8e210ec7b205fe9e1c0886d335cb00a88a7bde8b800f0223890f09c60b9) | [`0xaad645…`](https://lasna.reactscan.net/tx/0xaad645062602f52b1d5549b1b6352283deb463bc6309932602e335094c79de07) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 81 | [`0xbafb27…`](https://lasna.reactscan.net/tx/0xbafb27e4414ec41ed19c1b77680839b098e4176e2425580e3e9ed611007eb252) | [`0xd52630…`](https://sepolia.basescan.org/tx/0xd52630b2afd12211b5fe3d81d3fde5e57cd31431badb1ce67d6187c66fba85de) | [`0x727797…`](https://sepolia.basescan.org/tx/0x727797abed49903c92fe17936f6dfced473e09dca160cab20396ec3d26c723ca) | [`0x2205be…`](https://lasna.reactscan.net/tx/0x2205be299279614cf0c977bff2ee85290eafd42ff60ba6b10a65fe809438ade1) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 82 | [`0x0a0d6b…`](https://lasna.reactscan.net/tx/0x0a0d6b265a70b8d379e0c6d952ebb6d17e97e2a006017c2e2ceea702c8b1698b) | [`0x8c3441…`](https://sepolia.basescan.org/tx/0x8c3441ea52a9e16c8aff52c5e38b1bdb8cb604abbda8ab93e5b5832d797a0b90) | [`0xe491f6…`](https://sepolia.basescan.org/tx/0xe491f6965537d0dbe094ce5ffa6897d02516094b16f233fac8cd9aa913d8f54a) | [`0x6ab9ca…`](https://lasna.reactscan.net/tx/0x6ab9ca861d92e08336d0060519de936163bbd2c0f0e98caa7329a8ab48d4a0f1) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 83 | [`0x0ff163…`](https://lasna.reactscan.net/tx/0x0ff1633a5f6b7b76748b8ac0597e1f31f6a5466f56b586889699ad44b92e068a) | [`0xdc8530…`](https://sepolia.basescan.org/tx/0xdc853065db7bc07e979cc4661ac636188835f0082dc5ba923ecc266c3749b1af) | [`0xf255e1…`](https://sepolia.basescan.org/tx/0xf255e16f0fa811cf7b9f18c5432fd3d1d9ece51dfd24061cd14e56c67f45c33b) | [`0xc364c4…`](https://lasna.reactscan.net/tx/0xc364c4c608cdde62c3bfd7a17dd83e22f05586aae8bfade61dd17c7bf5a0ec20) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 84 | [`0x6e2218…`](https://lasna.reactscan.net/tx/0x6e2218dc0498ed140a7338925db398dece765835218f0706c43e0251771f3592) | [`0x9c9012…`](https://sepolia.basescan.org/tx/0x9c9012f645bfb63551e8d8474d69dbade24c767e9f7098df5fd64f1ff2b55269) | [`0x461a7a…`](https://sepolia.basescan.org/tx/0x461a7aa35c3d3ce16cab04a88d5a37b546f3334082ecb7829b66b8259805129e) | [`0x9086f6…`](https://lasna.reactscan.net/tx/0x9086f6cbe11ec9b496f8f259e7cbf4eb54c509bfac7e513d3cd69415a811b5c4) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 85 | [`0xacf7dd…`](https://lasna.reactscan.net/tx/0xacf7dda6717d14434f034ccb243c2ea25fedc0d3154ed88728aa4b12a80975ce) | [`0xfd53bb…`](https://sepolia.basescan.org/tx/0xfd53bb252d414a4e22f101fd5ce9a3647af7550ccca22d21399d3bb1ec98ea75) | [`0x12d670…`](https://sepolia.basescan.org/tx/0x12d670b1f2fa4df7b671006d580a872872aeceef11890b69c1bdfcc7724110fe) | [`0xa6ec9b…`](https://lasna.reactscan.net/tx/0xa6ec9bcf8454f16e974202d8bb3788fe7663e06c724308d597144d5e353f3c26) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 86 | [`0x0372f6…`](https://lasna.reactscan.net/tx/0x0372f6a93285338fbe2796796671aecff6140e85d02e3a70aef552245a609f51) | [`0xe7f445…`](https://sepolia.basescan.org/tx/0xe7f445b0961b2d95ed4a1859815409b1f54f6f10774499e84e530ad5f3bf9b99) | [`0x9b1cda…`](https://sepolia.basescan.org/tx/0x9b1cdaeb0f6eb7ddb1e1f1f6607c8ee0f0858ab197bca77a7d29f0f87f933e8a) | [`0x70be8d…`](https://lasna.reactscan.net/tx/0x70be8dfc001e6d6bb10c626586ff688a8662452043f163f3000b1a4634d37200) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 87 | [`0xdff458…`](https://lasna.reactscan.net/tx/0xdff458d91a9faa4d1f466de151c80a5c46df672072d8d585597a228c7ba848d9) | [`0x68ce82…`](https://sepolia.basescan.org/tx/0x68ce82ede35cf80b3e58354090736f35c063d6b69a619ad6ae16fd9fd012c87f) | [`0x2ad14c…`](https://sepolia.basescan.org/tx/0x2ad14c622a43a3e40c73cec5606f29b10f1f7183fc91c33395f427a3bca389ce) | [`0xa0ebb8…`](https://lasna.reactscan.net/tx/0xa0ebb8fb6ccba9b14340588b4aa554bc4a2bde1fdf9f0015ae00e2f3c67d2125) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 88 | [`0x747d0c…`](https://lasna.reactscan.net/tx/0x747d0caa7ff20bffea4054986bab4790397ebde96eaa467ed6296b3139f72cb2) | [`0x964018…`](https://sepolia.basescan.org/tx/0x96401850242386a94195066dd52c018d0e9d7c2cf170d680dba8b69c9c98924b) | [`0x41a479…`](https://sepolia.basescan.org/tx/0x41a479621322a456ea0b1494d8ef0222315b2f018a197f23da70a5b3d1ad0e57) | [`0xa152be…`](https://lasna.reactscan.net/tx/0xa152be79ece9c86ac580600a980366ccc469149acf86a62edd4a6086f1c23058) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 89 | [`0x00b567…`](https://lasna.reactscan.net/tx/0x00b567517ec2aab061f6bbd8c35208c908c9d198796f885d3d986dee9c4d3640) | [`0xc79fb2…`](https://sepolia.basescan.org/tx/0xc79fb29e006cb1dcda8f124e8b6b52aa2581f7dcfe77b418897739bb76e11c82) | [`0xda8ccb…`](https://sepolia.basescan.org/tx/0xda8ccbcaa69d322e0fae4cd02664b1ebf0dc68e4d7f5911e15a380043a51d2c1) | [`0x8d10e9…`](https://lasna.reactscan.net/tx/0x8d10e910eef6b8dd833ad80252de8d82504fb7f73019722dba6e01ca1e4447c1) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 90 | [`0x0ff415…`](https://lasna.reactscan.net/tx/0x0ff415a0247c556a2ac15dfbd718ba4d73fbd8327ae71b655d907fa70e7c251c) | [`0xcc9dfa…`](https://sepolia.basescan.org/tx/0xcc9dfa4a6a3cf827e9619052ccaca3112f7166f73577dcd781cf25c15ea3dcb9) | [`0xce5f02…`](https://sepolia.basescan.org/tx/0xce5f02431b60860e1526435009acb17055a0ac25a99004ff71eba6f3012b3e9a) | [`0xc90fab…`](https://lasna.reactscan.net/tx/0xc90fabdbde155430223692e887c95760f4f96c6704e0d096c50ca012f6e5281c) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 91 | [`0x27737c…`](https://lasna.reactscan.net/tx/0x27737cbfee1df81a974b35869914f92cec7fa3a1390a67f54af8cd93702f83dd) | [`0x7459f5…`](https://sepolia.basescan.org/tx/0x7459f58cc2ae36ff9cd2587486e86265e6af0cd392f5939e675eebf6b26d53f1) | [`0x69a419…`](https://sepolia.basescan.org/tx/0x69a419344126c55148b0acf2ed34653986d1b5d6eb2ebb4d81abb4ed07fc9a6a) | [`0x81bced…`](https://lasna.reactscan.net/tx/0x81bcedb69db0173926de3c593d8b1f7e6e0f55e822542ee75b5277782fa41b61) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 92 | [`0x97d6fb…`](https://lasna.reactscan.net/tx/0x97d6fb1410af75568d54dd443e45110bef398f248edf71225b8c388e6b4e525f) | [`0x0ffdbe…`](https://sepolia.basescan.org/tx/0x0ffdbe3b7d9c2a07ef77a5634dd1bcbd094176622dfcdafb3d318e60cb6759df) | [`0x2f1707…`](https://sepolia.basescan.org/tx/0x2f17072d3789556bd6734cbf194aa8c94cd7ef4351eeacff24e2a3539222aa50) | [`0x9e2e0c…`](https://lasna.reactscan.net/tx/0x9e2e0cf7f830596e8e5375ee4b5cb44adcdf42be65ad01effadefa18358ef27f) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 93 | [`0x09ac72…`](https://lasna.reactscan.net/tx/0x09ac726bd7959163961fb8a10943753a660a6c2d4a0a08713c27948725d769ab) | [`0xda46cc…`](https://sepolia.basescan.org/tx/0xda46cc31de56e728c41bcabaef01c551187d302c8e78c6a0182ff6edf4e68337) | [`0x191a1c…`](https://sepolia.basescan.org/tx/0x191a1cc52270f593233bef2c0b531ef1c29a8c067d3828fa65c8bf6622f1808c) | [`0x7562ad…`](https://lasna.reactscan.net/tx/0x7562ad562879d5cb01651b941475d978e00bf327acda647ba71dd632d5f9f61c) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 94 | [`0x23f2f8…`](https://lasna.reactscan.net/tx/0x23f2f8b2671eb0b0f4d55fe0577abc6ddb819216a153a38785e61fabb971d379) | [`0x261181…`](https://sepolia.basescan.org/tx/0x26118139dea09a6fd728b797082e92398a3140c092c5da9f9c6373ac97c23513) | [`0xc9e85a…`](https://sepolia.basescan.org/tx/0xc9e85a8c680e995e57b26b94f461312e14d50e4d0926f27a59673749559e0478) | [`0x5a8cd9…`](https://lasna.reactscan.net/tx/0x5a8cd9c90015a2011d858a0df0742f3773f09388e61ca13353dcf74c15542998) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 95 | [`0xf3ca2b…`](https://lasna.reactscan.net/tx/0xf3ca2b1b682afad6b842cd4b16d9e15ecfc9493d88fb778702556f9153d3c72b) | [`0x852ff8…`](https://sepolia.basescan.org/tx/0x852ff8cd4f05dd1ae6adda224f1dfd165c9c1bba2f18d619ffd7419227eaf354) | [`0xd0da4d…`](https://sepolia.basescan.org/tx/0xd0da4db7266589af94797da918865ee781327624635061c5504a5e7f577ab80f) | [`0x42690a…`](https://lasna.reactscan.net/tx/0x42690adfb2c05cc5fac5a628ab6860d80c0e20165072d0c011e8376972060ef4) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 96 | [`0xda8a0a…`](https://lasna.reactscan.net/tx/0xda8a0ab7a35fe20f882fe5f4238e92a8fa70ee2de162df14e4045ede6ce981c7) | [`0xc8c344…`](https://sepolia.basescan.org/tx/0xc8c344dea432e9ecf80da5e0a32a3382d3ea7081db92541a0f648f7a6cd774c9) | [`0xec25e4…`](https://sepolia.basescan.org/tx/0xec25e4a710cbdc0fe32507faf9385ba46a5eec5ced00c64bc1ba69223b8ffa97) | [`0xe7314c…`](https://lasna.reactscan.net/tx/0xe7314ce5ef0b0512a6621e9293364dd3c1526d88bf111ec3486bcd14cee25fd6) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 97 | [`0xb94bbb…`](https://lasna.reactscan.net/tx/0xb94bbbcd60793127626ded7a451ac39ccb7a0a3a11dbf1586ceb04a7bb764193) | [`0xcee36f…`](https://sepolia.basescan.org/tx/0xcee36f5050d38de6b5ae333a2251c516ceb5dd6187a8b1d75a0ce72165ab2423) | [`0x08dc5b…`](https://sepolia.basescan.org/tx/0x08dc5b6781ecaffd34bc8b93f11ed2dbc9f5f49908bcaccdd4cd6c07656d2f58) | [`0x7a5940…`](https://lasna.reactscan.net/tx/0x7a5940f603307728c646a3e34223be9e3cf736c8f4888a60cb2e48622b8916f7) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 98 | [`0x123a20…`](https://lasna.reactscan.net/tx/0x123a20b5aae09a4ba65a626c58db904715cb54a1ac15368fbc65e381f27faa91) | [`0xd22f66…`](https://sepolia.basescan.org/tx/0xd22f660841a4c1cf1dda6f5ed7da9734f7d5b4609091f8dbd111d865d9027d02) | [`0xbf994b…`](https://sepolia.basescan.org/tx/0xbf994bdce97d1b550ebfa5001bc74d9f8a47d5b384963b44ae4c00cd964fb329) | [`0xb27759…`](https://lasna.reactscan.net/tx/0xb277598d1cbbd0a36cbb9f4c068a7f30ed12fc53957371d8a0408e2204e7699d) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 99 | [`0xffc42f…`](https://lasna.reactscan.net/tx/0xffc42fcf7a5dfdb762ce5fc75b0cdc075c8762b011002493011046595546c07d) | [`0x8aa00e…`](https://sepolia.basescan.org/tx/0x8aa00eef03bd0be5315c863c51b4dcf11c9c51852c09a90ba9b286d9ce80a498) | [`0xd41d43…`](https://sepolia.basescan.org/tx/0xd41d43b06d721bef62de01e5051f2300eed08326f14edbf187c904617ca72645) | [`0x98305f…`](https://lasna.reactscan.net/tx/0x98305f9fcc7d73d573392263ca0bace8774713f3ea7c480b15ef62764563377d) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 100 | [`0x9dab28…`](https://lasna.reactscan.net/tx/0x9dab28b112bfaa0a58e9de78f474c14bc671e2ccb433000ed6a7813f5d1ce3a9) | [`0x0ecb5f…`](https://sepolia.basescan.org/tx/0x0ecb5f346e0ed119262e5f7605e24ba7aac581e5a34dd308e6eea7c8edd414fa) | [`0x12d8db…`](https://sepolia.basescan.org/tx/0x12d8db10454d9f43690d5106338cca96bfc8fe32f6db4a6407ad033cffc6fb6a) | [`0x2db4d0…`](https://lasna.reactscan.net/tx/0x2db4d0c5ea522ead1ce39899e65681d0d46192a5d0bab5013e78e13c06cb4e22) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 101 | [`0x50b3ed…`](https://lasna.reactscan.net/tx/0x50b3ede747afb52e6ef352d9c2eea73d9144f3087aaa003a4fe6e4dad9b0e347) | [`0xae37fc…`](https://sepolia.basescan.org/tx/0xae37fce254256dd392f5b5fb17a98ac1ab0274203e88e3f1fbd8f051f7b7311c) | [`0xfb5539…`](https://sepolia.basescan.org/tx/0xfb5539681ad00134368c07c6c14980475258e73f27c5eafe2386d3a26ba563d8) | [`0x46f43d…`](https://lasna.reactscan.net/tx/0x46f43d62ff188d207b55fe4f86014150c4c3fbd6c19a50fe6e4cfe150fc903d6) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 102 | [`0x43afbe…`](https://lasna.reactscan.net/tx/0x43afbe8618a1cc3a2c4de26c6f594646cf05cffc9d495901a4c662a3c61312cb) | [`0x0c60e2…`](https://sepolia.basescan.org/tx/0x0c60e2ccc39fcaf46d105af2ccab62566163c7b98ed3ce51f1b55a8b68bf5992) | [`0x4cdee9…`](https://sepolia.basescan.org/tx/0x4cdee9a0bb1d73ee64a0b2b704758e8f81b2f0aea3aa10cadcb47a9c4156fb98) | [`0xcc3188…`](https://lasna.reactscan.net/tx/0xcc3188d7f844df38779b19fdfefa344cc4253ab6b3c1bf5663b76bc22a7be891) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 103 | [`0xfb65df…`](https://lasna.reactscan.net/tx/0xfb65df7e48840fa30092501b3cdde9b07a3d0a01a2fbeab9f0cf2bec3cba795b) | [`0x8cbc6d…`](https://sepolia.basescan.org/tx/0x8cbc6d0dc45de15f339fe961027cbf5282303c40aa69dde59b4aeccf95a35e17) | [`0x944700…`](https://sepolia.basescan.org/tx/0x944700573ba21388c216d1cfbc303a13b1eb7cbd910f695975d73e9b8feeba15) | [`0x773848…`](https://lasna.reactscan.net/tx/0x7738486bf7ce0c193ec46c9ba9b11ddad203b273d8fa4eb73a3d0a85cc1b1796) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 104 | [`0x11906e…`](https://lasna.reactscan.net/tx/0x11906e671c338789d0be968addbe9d6b94c5642ebd8968e554df5a15748fce86) | [`0x3ddd0f…`](https://sepolia.basescan.org/tx/0x3ddd0f80c11ae37f21d7ce47f6f1381b6b5a61c8aca96f6b7f29fb21d1c80474) | [`0x5b6a65…`](https://sepolia.basescan.org/tx/0x5b6a65a76bd900be09c52abd3e334156a7172f5d2f7fd816161a4253dbde6b2e) | [`0xb6899b…`](https://lasna.reactscan.net/tx/0xb6899b022d607ccfc5a9e54ae500154175a39c6de79f7d8a159c310e43342606) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 105 | [`0x37044d…`](https://lasna.reactscan.net/tx/0x37044dd5d01fe334a04e400fac6c864312f76481bea1b4a14b18b2a63d32ca21) | [`0x955f2c…`](https://sepolia.basescan.org/tx/0x955f2c42fd57483099a47c419583de17a53dd0ed7fe3e2f514be756ee5f307bd) | [`0x486a47…`](https://sepolia.basescan.org/tx/0x486a470d9e03351a09aca634414d95207eeec012149874d3bc7cdf39122d6746) | [`0xad39f2…`](https://lasna.reactscan.net/tx/0xad39f20b2ed8e367dcda31e20a0e88eee575e59aab16ba49941bd0bcc6b2beea) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 106 | [`0x436c99…`](https://lasna.reactscan.net/tx/0x436c9908ee66150e9831f588364a8754784f149dcb71e0f620b59eeecfe9b4c9) | [`0x0aee5b…`](https://sepolia.basescan.org/tx/0x0aee5bcea6868d3b354cb930c8378b488ba90f4e6ed3bbbdb69da3ce060f3888) | [`0xe5858e…`](https://sepolia.basescan.org/tx/0xe5858e5b2c07883d9fe96899570a9a703bd8aace7c4b863c820ad59c02da0f01) | [`0xe64ca3…`](https://lasna.reactscan.net/tx/0xe64ca36f8fe47eb1989755f8dbd228cdb2b53cfda9a9af9aac42ad1ead4a6c83) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 107 | [`0xf7ba8b…`](https://lasna.reactscan.net/tx/0xf7ba8b132583e03258b4085f971f8f14e02ae607c3cfa0d849579b071d54b84b) | [`0xab9728…`](https://sepolia.basescan.org/tx/0xab972801fee95c1fd35a2384862e548648b6c0d4fad354b8b4711fd14815ef02) | [`0x11d6b0…`](https://sepolia.basescan.org/tx/0x11d6b0cf4201a373f31237e131977635d58572002e6a541c1191d3a98416ac2e) | [`0x5c2478…`](https://lasna.reactscan.net/tx/0x5c247842e522e6b21bbfe4a73248fb137693f543cb29256551f65e87c310633c) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 108 | [`0xb1c624…`](https://lasna.reactscan.net/tx/0xb1c62462b580ec7b101bcc354c1539ea28703c12ce3da4f46c84dba460f4b84b) | [`0x097809…`](https://sepolia.basescan.org/tx/0x0978092e740e2775c02383e7c6424d0d2e26a681fc9cb284da50139a1e72f022) | [`0xe2a8a5…`](https://sepolia.basescan.org/tx/0xe2a8a5d7559e607e1bf184c91eab77390a81f234a10fcf262f0cef28e893c70c) | [`0xb3f95d…`](https://lasna.reactscan.net/tx/0xb3f95d0b2f341af65bb3d5c61f3aa594755276c7475d00cdde8eddc8cb0596cf) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 109 | [`0x0bf5f1…`](https://lasna.reactscan.net/tx/0x0bf5f1e42c15f046a4534c0928a6499c99d928983bb64362b7d19ac8e878dabe) | [`0xd8771d…`](https://sepolia.basescan.org/tx/0xd8771dcee5365f84fbd4eeb5be1536a08f10053638755b427f3cdf57f5a2eaec) | [`0x4dfaa3…`](https://sepolia.basescan.org/tx/0x4dfaa3867d2b1435ae52e83ab22109699a2d20ff68a07a52afb06332d444d740) | [`0xedb917…`](https://lasna.reactscan.net/tx/0xedb917555ae21fb603906132255c8ac6b49a455e7acdafe4fe7852a221dd107d) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 110 | [`0x840301…`](https://lasna.reactscan.net/tx/0x840301ce23c19232e9bf1015200951c2600ec7008a0f8af8194d82fef1b52d3e) | [`0x25ed4e…`](https://sepolia.basescan.org/tx/0x25ed4e1293e50a460892ddc85022013a0a0540add32a311a84c95eebb2d8f558) | [`0x082dc5…`](https://sepolia.basescan.org/tx/0x082dc5c3b039b1fbbe042f4b5033739062a66501a3c61e67c006b4fd110079a9) | [`0x72b7ee…`](https://lasna.reactscan.net/tx/0x72b7eea833452359d110c407c66979108fb60ad1a92100231b8abfed5c13f518) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 111 | [`0xbf5735…`](https://lasna.reactscan.net/tx/0xbf5735655d7c522a6ec0e1a9ba88e64aac8604b665f0717bc0eab747c5727993) | [`0x0a6ce7…`](https://sepolia.basescan.org/tx/0x0a6ce7b71e165af0f6e86c6db62bba9275bc0ca919a097f7df124e8769fb764f) | [`0xcc5619…`](https://sepolia.basescan.org/tx/0xcc5619abd3eea3da2fa2140192f5fba70756a71c280f275564c5ca4268b029ad) | [`0x7458ff…`](https://lasna.reactscan.net/tx/0x7458ffad45e4874db90a13839067c978663006875c9ed46c3ea4d2e05002beab) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 112 | [`0x435dd1…`](https://lasna.reactscan.net/tx/0x435dd1adadc3f7211475093441168647eb1580cdf1e126ca08bf8e89c8d167f1) | [`0xe0f990…`](https://sepolia.basescan.org/tx/0xe0f9903e6f450771b7d695911632cb40872e11a54a48e9559bdc14de48dd7749) | [`0x330bcd…`](https://sepolia.basescan.org/tx/0x330bcd8df2a8c00bf4d20d5a5f99eb03d581de02891939f0fc45f06804f5837f) | [`0x745e7e…`](https://lasna.reactscan.net/tx/0x745e7e0a0b573117c6118fe528edeebcb87945217f53002a751bf786af61b4c7) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 113 | [`0x92c3bd…`](https://lasna.reactscan.net/tx/0x92c3bd0e5585d13b008c9de878f30a4300c0b82318955b50a8e71c627018cf71) | [`0x90f4b1…`](https://sepolia.basescan.org/tx/0x90f4b101b42ee411a6b8b5df5f79da42e384665f85e8d79899d49f70e27a108e) | [`0xb10634…`](https://sepolia.basescan.org/tx/0xb1063475999beeac9b659e2e5b65554ad4e1350b4b2b2c18ed9518cf590cd66a) | [`0x65e716…`](https://lasna.reactscan.net/tx/0x65e71639b49f5797bdc1d802d427d8ca3ec537c47b01dca283fd5ce34088b69c) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 114 | [`0x98c376…`](https://lasna.reactscan.net/tx/0x98c376c5e4621c7d28f4a9719243d6e6e8701074c7b17599d0d2323b22a6dc31) | [`0x00e230…`](https://sepolia.basescan.org/tx/0x00e230c48fecfb412f9469234b831df50b92e0a8cba293d629f1a4d3d909be54) | [`0xee465b…`](https://sepolia.basescan.org/tx/0xee465b3bf4b92cc602eabb1313410df0c04d87153cb2587a1040d84916584cbb) | [`0x8cc150…`](https://lasna.reactscan.net/tx/0x8cc1503353f08fe81c38a440ddceab3cc1b8c1ce3c7a4caa730a9cb860f291e9) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 115 | [`0xd7ae95…`](https://lasna.reactscan.net/tx/0xd7ae959cca10a5a97dfc7a86d458ce7f7e4ca1b5b9acb968ea854eee6749ed7f) | [`0x6beb2b…`](https://sepolia.basescan.org/tx/0x6beb2b3c74868c26ea8be8e2b77f655f55cdc110146820bc9ce4a335cf848e52) | [`0x29feed…`](https://sepolia.basescan.org/tx/0x29feed5f120adc024a8d7bb6ba5136b91c80121ab1223c4d3fc824876ff2a571) | [`0x3c687c…`](https://lasna.reactscan.net/tx/0x3c687c8f53bd7cb5a1222c690c2473367528548b192e5c87b4acf306c7fc8f4e) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 116 | [`0x36b994…`](https://lasna.reactscan.net/tx/0x36b994408c63ba899219aaa162df0e16934661b11a46f7cfc9b63c127b21b1d1) | [`0xbd4d8e…`](https://sepolia.basescan.org/tx/0xbd4d8eed1e68e27e4b48773c4cc880dde19cc28aad8039e9078639c6567b7c04) | [`0xfbeac0…`](https://sepolia.basescan.org/tx/0xfbeac05d99e9b3367758c3bd26a7ef16d14e48e2a9161a8cb3b4583f2c441131) | [`0xe6c110…`](https://lasna.reactscan.net/tx/0xe6c11032d38055a286f7b640b41985d6754454bc477f73c1d2c5160a2fb56d94) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 117 | [`0x7375fc…`](https://lasna.reactscan.net/tx/0x7375fcef2c5c6b1f006539786279e353b592c6352d2b64745d9b556d17147b48) | [`0x2e60d7…`](https://sepolia.basescan.org/tx/0x2e60d7f2117fdfe22fc9eb7ee33ac80cdf9553827517d27ecb500405dd8cb721) | [`0x2cd40b…`](https://sepolia.basescan.org/tx/0x2cd40bc8ca6953f61f8082e1b1e0c82619b731d1cfaf61c2a97cc6e7e19b04d3) | [`0xbe9712…`](https://lasna.reactscan.net/tx/0xbe9712d878a303159e3ea81424c2554a9e0abb0670b666e8582fa99a9c3d5e0d) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 118 | [`0x1fa50c…`](https://lasna.reactscan.net/tx/0x1fa50c4ee27c68644e998e44358ef7a5f8856be13c39cb8dd33d394854794d9d) | [`0x546773…`](https://sepolia.basescan.org/tx/0x546773c4ad39c79e972044657ff5918d0f8b65d195ec0856696f4b60808461f4) | [`0x6784f9…`](https://sepolia.basescan.org/tx/0x6784f9e40c185e99c35e1a539af013564b164aea3f6b5b5fa2f02ee19711b109) | [`0x46bb13…`](https://lasna.reactscan.net/tx/0x46bb13b0e048ee666bac112a7f41f72fca005caa8235e2bd0acad7eccac3f0c4) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 119 | [`0x9c9e31…`](https://lasna.reactscan.net/tx/0x9c9e317c952ccc7c575e1fb7a4f346bd2c9a1cc7af3569235ecc029d3fcc9d52) | [`0x17d74a…`](https://sepolia.basescan.org/tx/0x17d74a33d8d83fa662c9ab20db58feaab35c7dc2b9925ef297f4aa3e0e69a791) | [`0xfa2877…`](https://sepolia.basescan.org/tx/0xfa28774def50476d4988ba4f33769659884402449c2d8f9bbe927356b744445d) | [`0x342942…`](https://lasna.reactscan.net/tx/0x342942b99d21bef3a62fd51631208e6447d9c6bb01f8fd1f6f8966d6138f0305) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 120 | [`0x92aaf5…`](https://lasna.reactscan.net/tx/0x92aaf50cd9f6d9ea00b292f91a10927b3da25f8f6b6f2bac5516b35dd16fd400) | [`0x6137e8…`](https://sepolia.basescan.org/tx/0x6137e88a71d8f1bbd7ad56e7a18478e3af5791523c98cc96c920daaba690c9fb) | [`0xc4c02d…`](https://sepolia.basescan.org/tx/0xc4c02d1ba8dc08a89e8c4794808217d23eb293808d1d18c443193152b7ed78ff) | [`0xbeba63…`](https://lasna.reactscan.net/tx/0xbeba631437f08b6f40b5eb1484674dbaf821f4c91a8a92d906048aefffa54a81) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 121 | [`0x58020e…`](https://lasna.reactscan.net/tx/0x58020eeadd4d2ed5409d8370a103b7f9af8746387d6209e0c333f41dd4739502) | [`0xfa3b72…`](https://sepolia.basescan.org/tx/0xfa3b72f8b509c481f37c7f293719f88b9a7097f117dfa37e5577d8ec29e468ab) | [`0x3ade34…`](https://sepolia.basescan.org/tx/0x3ade34114b2854ed666639384452d4658324fc8d994511f732ea76de1d9096f6) | [`0xebf899…`](https://lasna.reactscan.net/tx/0xebf899b553397411384dcef7f1306e1720de15e485301a546c2da137c327f2c1) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 122 | [`0x2875a4…`](https://lasna.reactscan.net/tx/0x2875a4baa84018f03ff9ef5977088ac8071002e6788ba79d2df2563f88a1eddd) | [`0x29a942…`](https://sepolia.basescan.org/tx/0x29a94264af9f27155b37e44b1a8c54c568905034d7299465298a4f774204c5d0) | [`0x457c4f…`](https://sepolia.basescan.org/tx/0x457c4f422c38a825901c3a1ab716bc812658389a4b53a754221cd9b16cadbd6f) | [`0xda7291…`](https://lasna.reactscan.net/tx/0xda72916d525b4fa39602548fdcb8f38401e4e1463299204a1cb663fad233cad8) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 123 | [`0x650956…`](https://lasna.reactscan.net/tx/0x650956d57b2c05d3fcaf3f449b99a5fb7cafee34cfdbb8ee7c1bde5d1e7c5396) | [`0xaa1b78…`](https://sepolia.basescan.org/tx/0xaa1b78ea6c47956ce1682bba4ef935887a4bf9068de93d98fe9c5057512df2d6) | [`0x7409b3…`](https://sepolia.basescan.org/tx/0x7409b314f54e57e1aa3fdc3e695f24a555e10cebc3fe7c2348d47cd927f6d3aa) | [`0x7bcf73…`](https://lasna.reactscan.net/tx/0x7bcf73364a9d4ace71f87f1d678fdee2848e03136ffbbb1619b981bec58b1685) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 124 | [`0x6fb38f…`](https://lasna.reactscan.net/tx/0x6fb38fe4e88995274935203be2c777ee5bdf7e16e3325272c5a02e7fa9e618b4) | [`0xb997ac…`](https://sepolia.basescan.org/tx/0xb997acacf749e2bc1ebdbf496283efe00f09f4ec634e37455223025370edc9a4) | [`0x1724ce…`](https://sepolia.basescan.org/tx/0x1724ce8277d970e29956d88b3504b1e3901218cf35ebf9d8729c0431db6cfe0c) | [`0x43cda0…`](https://lasna.reactscan.net/tx/0x43cda0a829bd54e449c085d0ec140e6359de978887127b7e73c8e8e815bbbacc) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 125 | [`0x3aee86…`](https://lasna.reactscan.net/tx/0x3aee86383612969410be44cd421d9a83e92ee12505822f4cbfd59428ae3dfd3c) | [`0x9a0a62…`](https://sepolia.basescan.org/tx/0x9a0a62ac83ddfa5565eee258635464e5ffc959e9a550aac00f3b7b476e87ff91) | [`0xafbc5a…`](https://sepolia.basescan.org/tx/0xafbc5a956449ada39d73b41283413746f79793b26f6b4427b50162999bfbcb68) | [`0x525352…`](https://lasna.reactscan.net/tx/0x5253526d3a0ebb5aa9947b00cae1a9a1c8baca71fa913f73a2008a372b331eaf) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 126 | [`0xcdd87d…`](https://lasna.reactscan.net/tx/0xcdd87d41de3c6de0190920bd162284bf18782ffb09c2c754a9d1a8ff7aec611d) | [`0x00e9d9…`](https://sepolia.basescan.org/tx/0x00e9d942094e77cb1e68fb2466eee4825dad72e71d682628ef6cbf190d2e0aca) | [`0x61e822…`](https://sepolia.basescan.org/tx/0x61e82273a905fa38cfd71e0f9fa3ed7bfba2f7cff4e318f7d6e79d096f780a72) | [`0x9b1b35…`](https://lasna.reactscan.net/tx/0x9b1b35e37a752128a882730a90e195c83e35bc184e890c9a2d8073f45f91f56f) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 127 | [`0xc39db3…`](https://lasna.reactscan.net/tx/0xc39db3fede8009c2ff55d60023111b8ccaf83d3a05895726ea7ecbff2e88100f) | [`0xadbaa3…`](https://sepolia.basescan.org/tx/0xadbaa32f07133aa1dd586cd40c968ef0e4c06aa5693d882337d20a553340e54c) | [`0x759813…`](https://sepolia.basescan.org/tx/0x75981332bfb73bb1fb81ecbac0861e9100a074c723fd22bb5f24f39685429276) | [`0x5f5a15…`](https://lasna.reactscan.net/tx/0x5f5a150e7f5570e2d4359713b60b68f2e2313d988fbaaa1778217ed1aff963a2) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 128 | [`0x6682d4…`](https://lasna.reactscan.net/tx/0x6682d4a574e05e493ff5a582be9d03356f78958737aa4bc1e6ed43436c0935da) | [`0x66bc56…`](https://sepolia.basescan.org/tx/0x66bc56199ec3fc0f35a8e01e8dd009ea01607c239dd649193a5ef9c10db52803) | [`0x1e6b48…`](https://sepolia.basescan.org/tx/0x1e6b485ec56b92bf8c5625b24da6efa364b726b4feebba2503b4668f62290f1c) | [`0x42787d…`](https://lasna.reactscan.net/tx/0x42787d5eae566d3453cdab6c48fa787f647fe7d1364a0b898839e741c4f856e7) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 129 | [`0x220fbc…`](https://lasna.reactscan.net/tx/0x220fbce245cd7dc67124248170a743593156a40ff8c9e7bbca9b9432cdb3a582) | [`0xa9bd96…`](https://sepolia.basescan.org/tx/0xa9bd961ee11090de72ae441bb44b60bb0e938431018a883d776e44fc17cbcb37) | [`0x40c79f…`](https://sepolia.basescan.org/tx/0x40c79f92bd87fbfef57f38166a84533b0d5b6a4224d642499ffbb8be3f0e348e) | [`0x60842c…`](https://lasna.reactscan.net/tx/0x60842cb6eadb9a36d043a0b0547d1ed22a0e9108dda80321d25475d41a6cceec) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 130 | [`0xde8cbb…`](https://lasna.reactscan.net/tx/0xde8cbb64ff9118afcc6ce4d87e203083334f512f933eeea6505d134736809286) | [`0xffa8ba…`](https://sepolia.basescan.org/tx/0xffa8baf4310ebf0271d2e272f922cb30287fbaa8f3b1203a4affd305d77bb89e) | [`0xbb896a…`](https://sepolia.basescan.org/tx/0xbb896ad7cdbee00050e8e36361c8f05b908a4d406a4eee46cac89ef3f25c55e5) | [`0x170f5e…`](https://lasna.reactscan.net/tx/0x170f5e8ab33f257da28e36eded49ff013e4f3720817e9f08fcb0d6daabb985f3) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 131 | [`0x7d93f9…`](https://lasna.reactscan.net/tx/0x7d93f944838f28e99a4bddf8b4e07992346f37fcdc21f8449da99d56c04b3faa) | [`0x2e0c15…`](https://sepolia.basescan.org/tx/0x2e0c15b414974470304ccfc72f0efe2293aa55048c5812b7e78d0cd7cbbcba5a) | [`0x6fc24c…`](https://sepolia.basescan.org/tx/0x6fc24c81589ae7c3e910c84d8fb89b293be1bab14c273d38fac58a531118fd02) | [`0x62d084…`](https://lasna.reactscan.net/tx/0x62d0846f5aff05e0081f4a74e9cfe82c74e99ae496cece4d8b98a050c30e8ade) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 132 | [`0x571b83…`](https://lasna.reactscan.net/tx/0x571b83932ffaf69f3587edd59a23e239d00383bf7791e1ef3e8a1a5d6d88932e) | [`0x951b76…`](https://sepolia.basescan.org/tx/0x951b76d0053a35d7eb28cb485740da2271654feac90ddc0e91c27d5f5cf88389) | [`0xe21af5…`](https://sepolia.basescan.org/tx/0xe21af5a8f27a0b6b3716fb2e7788658d6ebe18cde64f4197306b371360927ba2) | [`0x66fdb8…`](https://lasna.reactscan.net/tx/0x66fdb82b9185c0831f42a66611425f7493e5d932f3a8c7824d49b814698becbe) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 133 | [`0x056dec…`](https://lasna.reactscan.net/tx/0x056dec326b55add1def1bf5995b9afa230d14ea36442971f8ab1cbe6b2edba70) | [`0x30dbd3…`](https://sepolia.basescan.org/tx/0x30dbd3e7f224ebe77a4479d5465f4f7284e41acadc03780e1e77d327106c0abe) | [`0x22c5c7…`](https://sepolia.basescan.org/tx/0x22c5c7205ee000ecd6604201d723cad11ae31bec17d4eb2eb9e29304c4328b9d) | [`0x871c38…`](https://lasna.reactscan.net/tx/0x871c3877822a89461208c4a748b3cd78514867363837a59b06dfe66868e44ca8) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 134 | [`0xc2d521…`](https://lasna.reactscan.net/tx/0xc2d52179130e34d0d398ad81b7e48a217158a17fa1b22eeae3f9b2cfcc35d8d8) | [`0x71c7ad…`](https://sepolia.basescan.org/tx/0x71c7ad2c448e951d0af702524526c4031c1625d72ece787991a20fc87bcf5b27) | [`0x8254a7…`](https://sepolia.basescan.org/tx/0x8254a73d42e95637c295e11b5969d4daa13070924fa70a70fe79a481713d97d4) | [`0x60b14d…`](https://lasna.reactscan.net/tx/0x60b14d76036620d7857fde185f61949b1d0445f546e69537b6040567d338696a) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 135 | [`0x4923b7…`](https://lasna.reactscan.net/tx/0x4923b7ddaa7fc299bf29ceb36597e2978817075ea2646126b1e7105a3ce990fa) | [`0x25aa52…`](https://sepolia.basescan.org/tx/0x25aa52b90f59925b6517c85b90ccd3b043375567cac14a693be7caa54ba355ce) | [`0x26ecbc…`](https://sepolia.basescan.org/tx/0x26ecbcc043ab94b879c478b78df3ad96ab49f46a2fa13e51bc388df84880d9fe) | [`0x29d190…`](https://lasna.reactscan.net/tx/0x29d19049182128af67b15bcd0e70531340926c8b644c9b8e2b6d928aad45e423) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 136 | [`0x1d8ffc…`](https://lasna.reactscan.net/tx/0x1d8ffcabed98d4d54e7cb55da56ed83087ab2ba7ed2ab972f75a347cc2c13a15) | [`0xde0d43…`](https://sepolia.basescan.org/tx/0xde0d43dddae853e339cb1aa400cb01a92d8adb7f918b500155229bed4643529c) | [`0x86bfe4…`](https://sepolia.basescan.org/tx/0x86bfe4c3cc4ff5b2d1800ead93caed6daa674821b46a38563d86005a9284336d) | [`0x2af64c…`](https://lasna.reactscan.net/tx/0x2af64cb6ef7eb5c850cebb6bc55145137cce136df947763d8879b642e58fdb70) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 137 | [`0x1d2cca…`](https://lasna.reactscan.net/tx/0x1d2ccae9494220092cfb26df40be95294f2d2949fea6caffe32e4ef9eea6018a) | [`0x8594a6…`](https://sepolia.basescan.org/tx/0x8594a654acebc1bb484ded710bc79faf5dc62dbbeffc2fa4be6747ced073d6de) | [`0x751e27…`](https://sepolia.basescan.org/tx/0x751e27a137bf3b8b3c50b741db3563db235b86dda9554241d682dbbc6de761ff) | [`0x083b6f…`](https://lasna.reactscan.net/tx/0x083b6f74fde95718917ce81ba5d803164a91a78a0201d5b1f77bd6ffe886cd03) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 138 | [`0x1c0ea4…`](https://lasna.reactscan.net/tx/0x1c0ea4e21468d50a18fed5c2d0fa24b198381c17c1a08faa00a1202b3f8b56e8) | [`0x020ecf…`](https://sepolia.basescan.org/tx/0x020ecfbbf1e26ec60cd95376abade794e682a0990de08b4dc32b073538c414e5) | [`0x0c5d37…`](https://sepolia.basescan.org/tx/0x0c5d379a2ff69553e157d198824ff7f474d482c97659e909b734af4b00514f57) | [`0x882e1c…`](https://lasna.reactscan.net/tx/0x882e1cfc6a17c1d59acc9e3093182885d9839f9a995a4c2e526ded73cedf7e98) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 139 | [`0x761261…`](https://lasna.reactscan.net/tx/0x761261599ab062020ef498422301d8ade33533671b12b159efc354898ad1cc3c) | [`0x2f0fec…`](https://sepolia.basescan.org/tx/0x2f0fec8d71a3cf9f65ff9ea3d5d073b2b87167519d5ed9f8e998311d85887203) | [`0xa2bd46…`](https://sepolia.basescan.org/tx/0xa2bd46e7b56b3e9bb14840f29961ebd93db98652cb4de806652cab1dba538d01) | [`0x0a2de3…`](https://lasna.reactscan.net/tx/0x0a2de3a6dbcb2194fb20a90e40bf2172e8bbd88b5a545211f32c932466ce27c1) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 140 | [`0xbe7132…`](https://lasna.reactscan.net/tx/0xbe7132ea17b878ac1ea5a637754761e14269944203f488215eea8abec984449a) | [`0x9dc010…`](https://sepolia.basescan.org/tx/0x9dc010c9b0f087f52d53c19c9264926f3874b9d23d10882dbd00c4ff6bde1c87) | [`0x3c313c…`](https://sepolia.basescan.org/tx/0x3c313cc78aedee895a028afdaa2d42d3c12ba18879365dab0ace0751c67dfa2a) | [`0xae08c9…`](https://lasna.reactscan.net/tx/0xae08c98177c140df4353fad0d90c7a31634183b4553de324ee907648a7c9b9cd) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 141 | [`0xc04c33…`](https://lasna.reactscan.net/tx/0xc04c33bb33ff9cc3058018d1d90827170c85c789c9b2521180de197b6a40abb7) | [`0xa7a97a…`](https://sepolia.basescan.org/tx/0xa7a97ab514f9f75cd99fa56a50cd880b051c687ade81fae4508c8dac99427292) | [`0xd9a858…`](https://sepolia.basescan.org/tx/0xd9a8581a92faac44cbc584bc4d0bc6599e9d99f9ec1d24c00ba11bea30e8acd2) | [`0x586961…`](https://lasna.reactscan.net/tx/0x586961e9e3220134a2f016d7a37bb2f380a9660804710f78ad11a273eebaaf87) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 142 | [`0xca7bc1…`](https://lasna.reactscan.net/tx/0xca7bc12c74d2475d2130a7a1f9997cefaced7bb3994830068f635ec660bbffe1) | [`0x6bb053…`](https://sepolia.basescan.org/tx/0x6bb053c4b721ba56de8972d975d8bedbc2cf339789b8ae47cbfbae7d84c95bd1) | [`0x04c782…`](https://sepolia.basescan.org/tx/0x04c782905e3c50a9cb677b2aacaf55fa547d9e746ebdce1304bf4c68ce5851c9) | [`0x86bacf…`](https://lasna.reactscan.net/tx/0x86bacf1f2da4fb5201b1cb358c50755bd0c2be829cfbc97f514603dd41938cd0) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 143 | [`0xd1b630…`](https://lasna.reactscan.net/tx/0xd1b6300fdd08a55f35e51ddf3e9109f5063c50493b52f0172b4c65733a41abd8) | [`0x5beb71…`](https://sepolia.basescan.org/tx/0x5beb713df107e256966119e431922ae6d56ee2078836e0c74e98e85f5ce5c2ec) | [`0x0b5c34…`](https://sepolia.basescan.org/tx/0x0b5c34cf08436e926f3ac0901de34ae1e76f212cdde619c28f1b0a9c4738a6f4) | [`0x42e091…`](https://lasna.reactscan.net/tx/0x42e0910578f1fd7cc94a3415ce7857641caaffabe970661ad3bcc5f64311fb5f) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 144 | [`0xc9e0d3…`](https://lasna.reactscan.net/tx/0xc9e0d32e0a769eb8abc0a9c5d3bf219cfa304ff76930b279a77a6326630266f3) | [`0x2eb88f…`](https://sepolia.basescan.org/tx/0x2eb88f1acd1f4167d07828f8bdd83152c52e0d738d1a8913b8bd4b39394db732) | [`0x5756b7…`](https://sepolia.basescan.org/tx/0x5756b7c214f8f59d8ec30bfc32298e908a0c9eb5805343bbf982791931d82f97) | [`0x572f44…`](https://lasna.reactscan.net/tx/0x572f444b9f19db5a3f4923511e8aebd1e0991c68cdef4cd3415cd2496e2de4dd) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 145 | [`0x7222bb…`](https://lasna.reactscan.net/tx/0x7222bbc2878888eab0de64c8b30c3b8e71bedfbd7e723149247496233204fbbf) | [`0x109a74…`](https://sepolia.basescan.org/tx/0x109a748bff30799e4ae30afed1d6cc0caf188eccea8b4b6390024d30f8f165d6) | [`0xdda687…`](https://sepolia.basescan.org/tx/0xdda687be7b57b9d1f25926d1e1385017cbcd538ecbb38e21c4f28d9edb01ef9c) | [`0x6b99ed…`](https://lasna.reactscan.net/tx/0x6b99ed4989bcbb1dcdaef8b1f432a45384fd9321c4d727cf1ce47712a6c27f0f) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 146 | [`0x7aae1a…`](https://lasna.reactscan.net/tx/0x7aae1ac50ca4bc881dc07cf13ef47404e9f4175f0a130e588c84b747d0e7a2c5) | [`0x732d3e…`](https://sepolia.basescan.org/tx/0x732d3eff5ddec65043d87011ad2e160a3cf5f7c79043289a2f53d88e4d60aeb7) | [`0x612e62…`](https://sepolia.basescan.org/tx/0x612e625d15cdd4f0bd699c8daf786733f0f28d348e7129e26ec75b146f89399f) | [`0xcd3f68…`](https://lasna.reactscan.net/tx/0xcd3f680cd4afe912776951cb48e9d8ee9527d06b995f63915637031dd8b0e515) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 147 | [`0xeab5da…`](https://lasna.reactscan.net/tx/0xeab5daa48ee3c4ce11492b5379594fe6907cdf0fd8f87675e3112cedeeb0c0a8) | [`0xbd0971…`](https://sepolia.basescan.org/tx/0xbd0971e23beddf31dc81e516e3341e7cdbabad9c9bfd3771ee7c0a508f6b1a4a) | [`0x31d91c…`](https://sepolia.basescan.org/tx/0x31d91cd20b24c0da6efcbec5954f8ba6e7805c9b9f9d88efdafa4216bd3ac521) | [`0x87088b…`](https://lasna.reactscan.net/tx/0x87088bc72133fdd1476c4714cc81502bcf460ca3d86c72f0f8a116951f97fe93) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 148 | [`0xa60b40…`](https://lasna.reactscan.net/tx/0xa60b40493db633e55159b64911241f6c098caccde0e40065c4e0d649cb297500) | [`0xf81da8…`](https://sepolia.basescan.org/tx/0xf81da81abe3e894ae64540b8aebc6c373d469603abd4fdfa82a57acd92065c41) | [`0x24a275…`](https://sepolia.basescan.org/tx/0x24a27565c7d6a5c29f953ca652a322e7f401bcc4711e172791d55293ea1c0052) | [`0x012898…`](https://lasna.reactscan.net/tx/0x012898bcd33bc714006c46b9ef29d15360bfbbc1087275b4f8f23550875a4189) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 149 | [`0x3c18e2…`](https://lasna.reactscan.net/tx/0x3c18e22462a6d25801c9bd4944ae4ee8e8171900c8d904913034dc44224cc909) | [`0xc85436…`](https://sepolia.basescan.org/tx/0xc854361444efaa8ec18c49166179e4f51b01e9214ad515777e5e54a93ee343bb) | [`0x1dfd0c…`](https://sepolia.basescan.org/tx/0x1dfd0c195e4b4bcc943be282425e4b354097b7c0d0c28d6d995a1c93e3af8125) | [`0x0f0aed…`](https://lasna.reactscan.net/tx/0x0f0aed968fe1dda76e53915925f58a1ddb9d5e8dff131cd440065a8e80147acf) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 150 | [`0x4b7e26…`](https://lasna.reactscan.net/tx/0x4b7e269b8ed28a4e3140a2183ff804bd763cf379052cb896d26a68fa76dc64e5) | [`0x37fbba…`](https://sepolia.basescan.org/tx/0x37fbba6ba30760b607de1dbb366ae16cd6a77a62a2d509ff1a9ffe39dd8e3729) | [`0x1226ca…`](https://sepolia.basescan.org/tx/0x1226ca589fbfb84a62fcd98b02137ed8afc9c57bd07ca95f2523a054298d215d) | [`0xa1fc3e…`](https://lasna.reactscan.net/tx/0xa1fc3e7b81a8a476dda91780b4a2c798e3aa0f23567a28ea4977b28fac53a2c0) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 151 | [`0xcc0914…`](https://lasna.reactscan.net/tx/0xcc091430433b080cda9bb594ee85532dd96670902225416651b9f2d76cedacc4) | [`0x6e9972…`](https://sepolia.basescan.org/tx/0x6e9972b47ad2260333d865a6ca7f84c0537b8e5d48abb2fc1b50182e001e1a2f) | [`0xfae914…`](https://sepolia.basescan.org/tx/0xfae91437956ca3c9b4c1f0facb599e85414deb2c33e2344e690fb6b343a5bb99) | [`0xae15d5…`](https://lasna.reactscan.net/tx/0xae15d527f551974e91b5939017fe4be2651af0f103e96cb7cbf39f205ff3bfeb) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 152 | [`0x0e4abc…`](https://lasna.reactscan.net/tx/0x0e4abc3be066c3785907e843a159363d94b48787cb9cbe7ea0de95437c60351d) | [`0x2205cc…`](https://sepolia.basescan.org/tx/0x2205cce430b7017204483d39a8532a893f9e52e3827cc78e815566b85a41fd55) | [`0x68556a…`](https://sepolia.basescan.org/tx/0x68556a39408325f22ca95435185e42b27abec25fd4b90089cc43d678bf7ec8b8) | [`0x7a8278…`](https://lasna.reactscan.net/tx/0x7a8278ea6ce204ae29f4fc31e7b6ecb438b94b1b990e98d80217242fd66a9864) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 153 | [`0xe60231…`](https://lasna.reactscan.net/tx/0xe602315c2e94606de59f4640ba28a0478a0347d29a9565bc8bc699029bce5099) | [`0x53badc…`](https://sepolia.basescan.org/tx/0x53badc065bc986c0d142d25c6bdfe8f6cdedb252661d6b14d97838aacd8884d0) | [`0x87a021…`](https://sepolia.basescan.org/tx/0x87a021770e6452eda252d7366f0cae500a2caf630b555b3768d375f5fcac38fb) | [`0x63e320…`](https://lasna.reactscan.net/tx/0x63e32030da5e8b8d0088476bc57d24598206095c87f01a08791f1c9e6a085e2b) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 154 | [`0x8e212d…`](https://lasna.reactscan.net/tx/0x8e212dbe823cf6d3e91441cff959143d7260979c1b15efa2b7a30abe840eead4) | [`0x175615…`](https://sepolia.basescan.org/tx/0x1756157eb863ab70f159fba33390ddb4bc127b40a84c42dd3a34eb84d5accfe4) | [`0x112e01…`](https://sepolia.basescan.org/tx/0x112e013d2afd6dd9227db90e66bc65449f67bf3bfb5f45ce1282f0dc15823d07) | [`0x81de87…`](https://lasna.reactscan.net/tx/0x81de87fe80451eb54209ba864da68d2bf4de01ef0be7323fa845251b9294b5f5) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 155 | [`0xe1e454…`](https://lasna.reactscan.net/tx/0xe1e454473ac50e9f5cb89a6806f6d74eb49a347287f2234f0090ee43d56689fd) | [`0xf8c6df…`](https://sepolia.basescan.org/tx/0xf8c6dfb7e3924a2308bfb911385fc750323ecf9bfe1555b87d3d8dd15d32dfc0) | [`0x54f1c2…`](https://sepolia.basescan.org/tx/0x54f1c23c970aa32ded100e6815a4e4115594d29ad5e6585e58c5bdc37d3c50ae) | [`0xf95db6…`](https://lasna.reactscan.net/tx/0xf95db6c7dce4f21905ccce1a65aa8d04ab35ffce1912434af56d3575daa16628) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 156 | [`0x0c9851…`](https://lasna.reactscan.net/tx/0x0c98510a5dd7bc6e7cf223ac330675ee19effebc06b528e8cf9e897f5e5ce66e) | [`0x1d1bc0…`](https://sepolia.basescan.org/tx/0x1d1bc0bdcf1a4f2a2b92c6a8cb49570049365b5162a5173d3758c52711aed9e0) | [`0x2e6932…`](https://sepolia.basescan.org/tx/0x2e693281cb459d6b3a651d28036debfd2dde0762a0423bb25add33121342b9c2) | [`0x0b27e3…`](https://lasna.reactscan.net/tx/0x0b27e3e5d7b5130d7a40552399ecc60a2c98ba7fc6cfab80828dce467cd26446) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 157 | [`0x6a8d71…`](https://lasna.reactscan.net/tx/0x6a8d7167c74ee2ab3c220f4d8407de9e2f03ac1a707c817f5ce881979d14e9c3) | [`0x3001ee…`](https://sepolia.basescan.org/tx/0x3001ee63b390f3b9802fa734a5884926b415c20ba741ebea044c6ea889237199) | [`0x27c571…`](https://sepolia.basescan.org/tx/0x27c571b2afbbbf070448ae76192043b49c05220cbc3978305a306866f78c4894) | [`0xa1aa44…`](https://lasna.reactscan.net/tx/0xa1aa44a1e7f30621b567369d2cece0977cb348bb64cc9c013c1d817899b2f197) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |
| 158 | [`0x87d950…`](https://lasna.reactscan.net/tx/0x87d950bb25e55c8e98b429aa540c362cb672df223bdc7e8452d444080daca5c4) | [`0x6d3fb1…`](https://sepolia.basescan.org/tx/0x6d3fb133679fff0fdb0342c4f18618e62d35faf5a9f9f838a11e9cb32abd5d22) | [`0x6f000b…`](https://sepolia.basescan.org/tx/0x6f000b51049a025269a43af1fc597d699d75f0388f9cf46c92b25cf890c56ac6) | [`0xa5d6b2…`](https://lasna.reactscan.net/tx/0xa5d6b2e4fb1bc1148201a999bf410d4c987f511058ba1197cda1e79ae5bdf07f) | no_trade | 7102 → 0 bps | LP_ABOVE_MAX, ECONOMIC_VETO |

## Every cycle, including the ones that did not complete

| Cycle | Outcome | Opened | Asked | Posted | Judged | Result tx |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | no_trade | [`0x838960…`](https://lasna.reactscan.net/tx/0x8389609044c23d05dfd4c9ee3e94a1dd2d8cf128d0ba192508bbc40b67cde089) | [`0xedb550…`](https://sepolia.basescan.org/tx/0xedb5507a8dc60a559397e4617f6804b37b0ee4e9cc58166c1a1d12f7423efc3c) | [`0x900015…`](https://sepolia.basescan.org/tx/0x9000153cff80d1d8d52263bfaffd42660c4657244d9f5ca779c0ee4d604a5b29) | [`0xdfa515…`](https://lasna.reactscan.net/tx/0xdfa5152aaac0e6c654ca358c6eba1866757ea3ce5e8361e12b7bce3d7018b651) | [`0xdfa515…`](https://lasna.reactscan.net/tx/0xdfa5152aaac0e6c654ca358c6eba1866757ea3ce5e8361e12b7bce3d7018b651) |
| 2 | rebalanced | [`0x01a2ab…`](https://lasna.reactscan.net/tx/0x01a2ab43f717831ff4a2b9d5092210d83e4cdfed9b4e206f0245c0be7a948c34) | [`0x01de5b…`](https://sepolia.basescan.org/tx/0x01de5b2b05cc5d4ce7baf896340c08462a0ff3c27d024aac62897eadce9476d5) | [`0x465a48…`](https://sepolia.basescan.org/tx/0x465a48e0fde71a2fafff5fdada8785ec42b4ce9129ab7ab169aae67d484dd980) | [`0xebd2fb…`](https://lasna.reactscan.net/tx/0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070) | [`0xd3e33f…`](https://sepolia.basescan.org/tx/0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19) |
| 3 | no_trade | [`0xdd906e…`](https://lasna.reactscan.net/tx/0xdd906e0099a1c04fa1eedd2e1509c4732fa910464ef4bf0dff0b8051ac7eed67) | [`0xc6c22c…`](https://sepolia.basescan.org/tx/0xc6c22c51b755c1041b499290d984f4561206c454418fd9593680d60ade911f41) | [`0x78ac45…`](https://sepolia.basescan.org/tx/0x78ac45223b61d2df05bf66822b4cb3876541a0313987c4fab3896325b0d56b38) | [`0xe5095b…`](https://lasna.reactscan.net/tx/0xe5095bf7ba8fc77afe15208c72b4a22734b002bf6ccf3ab66a96398595887121) | [`0xe5095b…`](https://lasna.reactscan.net/tx/0xe5095bf7ba8fc77afe15208c72b4a22734b002bf6ccf3ab66a96398595887121) |
| 4 | no_trade | [`0x0f3011…`](https://lasna.reactscan.net/tx/0x0f3011b01b04086e807f08aae69913cb3f6fb80a6450806ac97d2037e232d65d) | [`0x48e96b…`](https://sepolia.basescan.org/tx/0x48e96b95651b205c33e5a35671a4d7e36d26f33333a19a41f8becb0912c93bd4) | [`0x3fdb7a…`](https://sepolia.basescan.org/tx/0x3fdb7a21af31a7bdb23ba6776f3cbee4e46e95dd5fde98adba30b37198825f40) | [`0xad7c59…`](https://lasna.reactscan.net/tx/0xad7c59d88e7c046cbe629ad350537d8da1854437d51a38c6c8f2b0ac7b4a86b9) | [`0xad7c59…`](https://lasna.reactscan.net/tx/0xad7c59d88e7c046cbe629ad350537d8da1854437d51a38c6c8f2b0ac7b4a86b9) |
| 5 | no_trade | [`0x7c585d…`](https://lasna.reactscan.net/tx/0x7c585d89604141944322b385baf78b172dadd32bbcca79757603f840be72c73f) | [`0xa3382e…`](https://sepolia.basescan.org/tx/0xa3382ecea191cfb43f0e784ad9fb0f51cdc2b1ac3e2d1aef583681adbb0de45f) | [`0x91586b…`](https://sepolia.basescan.org/tx/0x91586b018684c8bf6258bc724da6f1a1ffff4f85635c4a45e20b0b85ac962f3d) | [`0xf8078c…`](https://lasna.reactscan.net/tx/0xf8078cebbf85185091b015728feaef7ad723da03dfdb698cc3110fb34f524d59) | [`0xf8078c…`](https://lasna.reactscan.net/tx/0xf8078cebbf85185091b015728feaef7ad723da03dfdb698cc3110fb34f524d59) |
| 6 | no_trade | [`0x2858ef…`](https://lasna.reactscan.net/tx/0x2858ef8165d436c0dfbee8a25aab921db82ac66b11dcf041feea109e8b030451) | [`0xda8eb3…`](https://sepolia.basescan.org/tx/0xda8eb3d48eb7d3fec87113ba9b84388576c947f8779ffa6e1a940e02447fe174) | [`0xfbbbbe…`](https://sepolia.basescan.org/tx/0xfbbbbe20c88f0ef2c4b8e35ea43b5721d7c50b7cf3effc0cfd92f786a01e2740) | [`0xa96ac7…`](https://lasna.reactscan.net/tx/0xa96ac77fdfa95cf907a31ffc6c25458b5828e423ced711790140ba05bd4c22fe) | [`0xa96ac7…`](https://lasna.reactscan.net/tx/0xa96ac77fdfa95cf907a31ffc6c25458b5828e423ced711790140ba05bd4c22fe) |
| 7 | no_trade | [`0xcc48db…`](https://lasna.reactscan.net/tx/0xcc48db98513d7c84fbf0b52ac4a498ff2d43b52416dd7a6750950cfa8b6dc6e2) | [`0x832474…`](https://sepolia.basescan.org/tx/0x832474cf4398555d1fbb47a0ddc3c315b7b1a7714ccf1ecdda70d0d978e883e1) | [`0x053c7f…`](https://sepolia.basescan.org/tx/0x053c7f1a75edc7e6aa53cf6f67f69bea79c760ca1542ef6c0d865300d275c988) | [`0x01a585…`](https://lasna.reactscan.net/tx/0x01a5856e731e104ba490893a883fab5712896c19bb57efb20c5e90ee90ad4c0d) | [`0x01a585…`](https://lasna.reactscan.net/tx/0x01a5856e731e104ba490893a883fab5712896c19bb57efb20c5e90ee90ad4c0d) |
| 8 | no_trade | [`0xc13c72…`](https://lasna.reactscan.net/tx/0xc13c7238ce95b80aa719b506883d12ed38544f254ac98c1d58b22d0ec9e4a9b3) | [`0xf7496c…`](https://sepolia.basescan.org/tx/0xf7496c0b744c3a3ccfebcb341360d6f90c611a87a32a57637bc0dd1c92a3d4de) | [`0xce42ce…`](https://sepolia.basescan.org/tx/0xce42ce6403a1b1e0321baf7589461b2109a142e7491141731fe433e047f9cce8) | [`0xe48045…`](https://lasna.reactscan.net/tx/0xe48045872db488e0a5e69ba62bba82c48c52d35873e4aa2dbf8fde3f44bf5c94) | [`0xe48045…`](https://lasna.reactscan.net/tx/0xe48045872db488e0a5e69ba62bba82c48c52d35873e4aa2dbf8fde3f44bf5c94) |
| 9 | rejected | [`0xa82eab…`](https://lasna.reactscan.net/tx/0xa82eab3f0b064e53a8db7012b1564b8bd0ea5e84c7783d165d44de00489a4834) | [`0xe8d13e…`](https://sepolia.basescan.org/tx/0xe8d13e1d9b1856ca53cd107e56663655c50371c71aa8f040eddec1c7cdf51e39) | [`0xe283b3…`](https://sepolia.basescan.org/tx/0xe283b3880634f2bf4d0e0394f07b77f6453548a7e09cd9fa9cefa57148762579) | [`0x4b56e9…`](https://lasna.reactscan.net/tx/0x4b56e9bed865264e93255c3f7476e08739bbc519b2ac1ef390e77435ca843f7e) | [`0x4b56e9…`](https://lasna.reactscan.net/tx/0x4b56e9bed865264e93255c3f7476e08739bbc519b2ac1ef390e77435ca843f7e) |
| 10 | autonomous_exit | — | — | — | — | [`0xf044fb…`](https://sepolia.basescan.org/tx/0xf044fbf02967a0ab057b3ccebf7f4a2464b261d190f166b299fabf4617fc34d0) |
| 11 | expired | [`0x4b2800…`](https://lasna.reactscan.net/tx/0x4b280093cbc5719a89275da7917513960e510511e26e7569c38b60f04744cd83) | [`0xe4f9df…`](https://sepolia.basescan.org/tx/0xe4f9df3e517ef059a5aa9b4fafe47386f2cf18b5e0f7d0b0e5c40bac88706692) | — | — | [`0x05a254…`](https://lasna.reactscan.net/tx/0x05a25404fb9d88e4fbc78434d66725236a6a95bb8db38b7e5481e5799c3882cf) |
| 12 | expired | [`0x05a254…`](https://lasna.reactscan.net/tx/0x05a25404fb9d88e4fbc78434d66725236a6a95bb8db38b7e5481e5799c3882cf) | [`0x3adcce…`](https://sepolia.basescan.org/tx/0x3adccedc177bc719a9d7ffd5cfa0b3ea05e763a9132d6c468b8a8f662514330d) | — | — | [`0x717966…`](https://lasna.reactscan.net/tx/0x7179665d346fc0daf87b8f43d659f7fc8dfb06c6412f1eccff51fcf9a2a33296) |
| 13 | rebalanced | [`0x717966…`](https://lasna.reactscan.net/tx/0x7179665d346fc0daf87b8f43d659f7fc8dfb06c6412f1eccff51fcf9a2a33296) | [`0x9d158c…`](https://sepolia.basescan.org/tx/0x9d158c84f144fdea206b5913c014e19137118c6b578b705fa13de7a0ee3771f2) | [`0x58da1b…`](https://sepolia.basescan.org/tx/0x58da1bf95d8bd7d1d37b2bc53b3629f82a5e8afd53cfab3f086dea379c3371e2) | [`0x544fe3…`](https://lasna.reactscan.net/tx/0x544fe3c634e9e32c5a3d6b480e03a90944f2ac82c41f43e4b48dcd68d0bebc71) | [`0x0439a0…`](https://sepolia.basescan.org/tx/0x0439a062a321d60cf7e506eb5c1f845c3954af7012b68db4d6a60c7051016ca4) |
| 14 | no_trade | [`0x2b373f…`](https://lasna.reactscan.net/tx/0x2b373f427a630ce00950a5a336ed683e315f213668db8cafa23fe13f3a23eb37) | [`0xbb2926…`](https://sepolia.basescan.org/tx/0xbb2926598f2dae68fd22fe4a5c8330fb40cdb1ca5af78bb44fac895edf7b2620) | [`0xd060a4…`](https://sepolia.basescan.org/tx/0xd060a4deffe3ec24d65638eb6d27e5b36a0d2be233b19e566928cd690c2f9d5b) | [`0x237e17…`](https://lasna.reactscan.net/tx/0x237e172aad28e7dc7286d0bb05f81d3425b7b449fa5656633dc6b3fc1f593fca) | [`0x237e17…`](https://lasna.reactscan.net/tx/0x237e172aad28e7dc7286d0bb05f81d3425b7b449fa5656633dc6b3fc1f593fca) |
| 15 | no_trade | [`0x0a60a9…`](https://lasna.reactscan.net/tx/0x0a60a9bf20841d4be0a4f3474ca30b05f003f4418be4eeb634cbe3a5ade97b17) | [`0x05daf3…`](https://sepolia.basescan.org/tx/0x05daf3cc08a24f6fc0990bd0007ee7e51db9ae51c027fc3b5c0b98291ff38fda) | [`0x820564…`](https://sepolia.basescan.org/tx/0x82056494d57bea079b74da750b3baa0751ebc7d7fce24eeac5de3c3d59c6de9f) | [`0xdfd54c…`](https://lasna.reactscan.net/tx/0xdfd54c6825796c7297d057af2500fc3a593545494c8482adc762c52bd62def18) | [`0xdfd54c…`](https://lasna.reactscan.net/tx/0xdfd54c6825796c7297d057af2500fc3a593545494c8482adc762c52bd62def18) |
| 16 | no_trade | [`0xf05e7e…`](https://lasna.reactscan.net/tx/0xf05e7ebac34d0566429b55c923aa4859d285cf5976136b84a022e9692b9077dc) | [`0xc78a48…`](https://sepolia.basescan.org/tx/0xc78a48bdc4b671ade7918f45670576ad91943de3a29959b32813f520f0aab91d) | [`0x0cbf21…`](https://sepolia.basescan.org/tx/0x0cbf21d7d296bd2c49227748bf3c2d2145602a5546f85cafc599989c7a275d25) | [`0x38997d…`](https://lasna.reactscan.net/tx/0x38997d63e281a6d18b913a45075d85ec87a4e48940163b6060ddba48b5a7f0de) | [`0x38997d…`](https://lasna.reactscan.net/tx/0x38997d63e281a6d18b913a45075d85ec87a4e48940163b6060ddba48b5a7f0de) |
| 17 | no_trade | [`0xf307f5…`](https://lasna.reactscan.net/tx/0xf307f534ac323bca9c1a8bf5b8d175d7fefe6dca198317342fc336e05f7ea7ce) | [`0x4e5917…`](https://sepolia.basescan.org/tx/0x4e591772a7ff4846312f463a8dee7d450c1401fc6513249b9248e48e309684fa) | [`0xb4aef1…`](https://sepolia.basescan.org/tx/0xb4aef1066b9c89680a5e43f4cef1321cb44c7a7ebdc747f78e9483d933ea543d) | [`0x0d32b8…`](https://lasna.reactscan.net/tx/0x0d32b81a7e97d1780d5d828e8a1d2388c57586b11be5d87bb86b1277cd073951) | [`0x0d32b8…`](https://lasna.reactscan.net/tx/0x0d32b81a7e97d1780d5d828e8a1d2388c57586b11be5d87bb86b1277cd073951) |
| 18 | no_trade | [`0xbe72b7…`](https://lasna.reactscan.net/tx/0xbe72b700e47816865a935d0fbf842019b2d2de44d8ad151fd41ad5943909df56) | [`0x488257…`](https://sepolia.basescan.org/tx/0x488257fa01baef580202525d806e5eb46ee7836601729848053b4f937e6cf398) | [`0x291885…`](https://sepolia.basescan.org/tx/0x2918857ae85f9593e65776f808443a5e2b0dae9d409d77824de75bc7eb12fa02) | [`0x98b0be…`](https://lasna.reactscan.net/tx/0x98b0bee7e0342d31b33e2c6e464dc3e4968168e1070e214b26d3303544434290) | [`0x98b0be…`](https://lasna.reactscan.net/tx/0x98b0bee7e0342d31b33e2c6e464dc3e4968168e1070e214b26d3303544434290) |
| 19 | no_trade | [`0x48de69…`](https://lasna.reactscan.net/tx/0x48de69ca6bb263bab7671538427a4b68a89a5a9ff32f89488bc42087c9ff8fc4) | [`0x397153…`](https://sepolia.basescan.org/tx/0x3971532dc9080b67ced7a16209ccefc981d1532b51d9465ecb444b9a54fc6e65) | [`0xcf2edc…`](https://sepolia.basescan.org/tx/0xcf2edcf151deb709140002e8ed7d37b23eb088ee4a83c8e4567650eba925d76c) | [`0x58acf3…`](https://lasna.reactscan.net/tx/0x58acf326434024c9f4f9029d96d5eef80b851f7427f2fe1ec306fea1f75af882) | [`0x58acf3…`](https://lasna.reactscan.net/tx/0x58acf326434024c9f4f9029d96d5eef80b851f7427f2fe1ec306fea1f75af882) |
| 20 | no_trade | [`0x5b09c5…`](https://lasna.reactscan.net/tx/0x5b09c51244f1b0fbd4a3995a8540d6efb8a8ffd855ca45e0f99d0aa4d8722a0b) | [`0x17b5a3…`](https://sepolia.basescan.org/tx/0x17b5a31a27b143f3e6cf6c260d84d3e96f1505b347312a1656b973f22d3b85f3) | [`0x351b5e…`](https://sepolia.basescan.org/tx/0x351b5e1cebe0e3a12b3ef6b42623856a78e8ab9859599458ef36369ed32f306b) | [`0x6fa4ac…`](https://lasna.reactscan.net/tx/0x6fa4ac4a9ff929d6d831fa3ed384a9c53f18c20226c5bb9d1b0d4ba18f757aad) | [`0x6fa4ac…`](https://lasna.reactscan.net/tx/0x6fa4ac4a9ff929d6d831fa3ed384a9c53f18c20226c5bb9d1b0d4ba18f757aad) |
| 21 | no_trade | [`0x2cf4f1…`](https://lasna.reactscan.net/tx/0x2cf4f10de921f8d585fd250798d2f64ee8ad4651bee2143b9684380d1e64d324) | [`0x518b41…`](https://sepolia.basescan.org/tx/0x518b419da1cd6f7a7d7fda1c339adaf0b3bf3bfa96bbb7e96aec5a3a320dbdfe) | [`0xf7f6db…`](https://sepolia.basescan.org/tx/0xf7f6db352d05400bb52aee9430fbc8955a449d7e357355171d1c521a5252fd11) | [`0xc9177b…`](https://lasna.reactscan.net/tx/0xc9177bd479c5d22bf9150c63e12f026a0c756cc1d638716e6fc769ee77a09492) | [`0xc9177b…`](https://lasna.reactscan.net/tx/0xc9177bd479c5d22bf9150c63e12f026a0c756cc1d638716e6fc769ee77a09492) |
| 22 | no_trade | [`0x789305…`](https://lasna.reactscan.net/tx/0x789305c5110c7deda4f62e37e5afac171028ad484c0215515aad34b733f44e27) | [`0x7e4f2b…`](https://sepolia.basescan.org/tx/0x7e4f2b08f96604eddf7ec3def229fc2c6269869a8fc3a346662e0f5a667612c7) | [`0xd6092f…`](https://sepolia.basescan.org/tx/0xd6092f07398d5c49610caea28267f5b1ad921bfa0e54a40bedef942bc19a9bd0) | [`0x75188f…`](https://lasna.reactscan.net/tx/0x75188f5de6aa432b30d8e0b18a5bfa301ca58c243d5b009c2991ebaf1ffd0be3) | [`0x75188f…`](https://lasna.reactscan.net/tx/0x75188f5de6aa432b30d8e0b18a5bfa301ca58c243d5b009c2991ebaf1ffd0be3) |
| 23 | no_trade | [`0x32e796…`](https://lasna.reactscan.net/tx/0x32e796c2f2c1390b2cfb11ed06679d4e28a2fcc20cef5f7b9be180a3143ea230) | [`0x7b9325…`](https://sepolia.basescan.org/tx/0x7b93256773ffedf681e60ce67a4f6185b68f47b37f81da439d8c4f71bda1ba3a) | [`0x9df282…`](https://sepolia.basescan.org/tx/0x9df282798bd166b96c29fc1db7d59111825bcb03b7fcdc42213a308e7f7e694d) | [`0x2735b5…`](https://lasna.reactscan.net/tx/0x2735b593f3b126a311d814f8ed8b12c10680aa77029c4683daa0885b0f9b19c6) | [`0x2735b5…`](https://lasna.reactscan.net/tx/0x2735b593f3b126a311d814f8ed8b12c10680aa77029c4683daa0885b0f9b19c6) |
| 24 | no_trade | [`0xe3c0fe…`](https://lasna.reactscan.net/tx/0xe3c0febacea9893274e2ffaf12675256b952c7f26e41bd3d9fb669b66a6ea302) | [`0xcc8112…`](https://sepolia.basescan.org/tx/0xcc8112832eaa936c9439e2ae4e134f0d379f8ce94557a2021336be40c9b7db5d) | [`0xc5dce1…`](https://sepolia.basescan.org/tx/0xc5dce1d99e3d03ad4c7d19d504da3aa2982757840753d9297139f1636141c264) | [`0xac771e…`](https://lasna.reactscan.net/tx/0xac771ea54e9f17c3d4589db616c7097683d4a5f0f8803fd7a1b2fe335f58dc2f) | [`0xac771e…`](https://lasna.reactscan.net/tx/0xac771ea54e9f17c3d4589db616c7097683d4a5f0f8803fd7a1b2fe335f58dc2f) |
| 25 | expired | [`0x732d85…`](https://lasna.reactscan.net/tx/0x732d85634fb2c200e1573b7de5fbe375897a6100c75bfb7c57e4f7bd1ccfda84) | [`0x5e292c…`](https://sepolia.basescan.org/tx/0x5e292cc84e07bbd282f8593068df17897735cd38020199ecff3eb11a40f8d597) | — | — | [`0x5d56bf…`](https://lasna.reactscan.net/tx/0x5d56bf9dae8ff90e10b390390bea564309996df7ffa007998fde048c8e98fe62) |
| 26 | no_trade | [`0x5d56bf…`](https://lasna.reactscan.net/tx/0x5d56bf9dae8ff90e10b390390bea564309996df7ffa007998fde048c8e98fe62) | [`0x464910…`](https://sepolia.basescan.org/tx/0x464910eeb06eff810a62bb2dd3b72912b943cd4132f3853404a8077b627cd88b) | [`0x490c74…`](https://sepolia.basescan.org/tx/0x490c7401e1795758ec1df4604fe787381c2cd076fcc3ade204ae6e202812b6e6) | [`0x012e5b…`](https://lasna.reactscan.net/tx/0x012e5b4995d6ff17967e32fb56e007cea7c09ac45135bcb4dace2d5505368522) | [`0x012e5b…`](https://lasna.reactscan.net/tx/0x012e5b4995d6ff17967e32fb56e007cea7c09ac45135bcb4dace2d5505368522) |
| 27 | no_trade | [`0x03388c…`](https://lasna.reactscan.net/tx/0x03388c596780925fb31d1610cde42663af28cd944721606a650cc9a36e7fae65) | [`0xbcd6fe…`](https://sepolia.basescan.org/tx/0xbcd6fe6f819560105837f2a25a3ea5e73cb8787a273ecc73aaab7a390c75a666) | [`0x84ccae…`](https://sepolia.basescan.org/tx/0x84ccaea95c2c167e4ef5a1427184c50ae04b570a8c7a973cde14535734829e37) | [`0x64d0d5…`](https://lasna.reactscan.net/tx/0x64d0d557cf9046e8946eab50a9fc7ea7ff1097d46a04151800696196e3bc56c8) | [`0x64d0d5…`](https://lasna.reactscan.net/tx/0x64d0d557cf9046e8946eab50a9fc7ea7ff1097d46a04151800696196e3bc56c8) |
| 28 | no_trade | [`0xc76c5c…`](https://lasna.reactscan.net/tx/0xc76c5c7bbd43a34172db584173f8d267506ec04aea4ae7db1a6fad8257ff559d) | [`0x57174e…`](https://sepolia.basescan.org/tx/0x57174e99d1bb1492dbe4bab6a2b9b935142dd91b61421dbd5e3ecc300995925c) | [`0xc7ff5e…`](https://sepolia.basescan.org/tx/0xc7ff5e227802d7ecb5353c1f91499edf7a89ba61451e79a772323651ce65a740) | [`0xdcea31…`](https://lasna.reactscan.net/tx/0xdcea313f8d571d5555760d9146391c3bae209246ddba198e86d1d2ae6db9ee86) | [`0xdcea31…`](https://lasna.reactscan.net/tx/0xdcea313f8d571d5555760d9146391c3bae209246ddba198e86d1d2ae6db9ee86) |
| 29 | no_trade | [`0xc12b8b…`](https://lasna.reactscan.net/tx/0xc12b8b38419c39ff9455b2a8b3beb5758b363aa21b8f4c34c6ef878dbda3e3e4) | [`0xa5ef36…`](https://sepolia.basescan.org/tx/0xa5ef368e26f85e8ba955f4a5ba3eca69cb4d6f6cefc7e47042fd21b3d13dcffb) | [`0xe12f6d…`](https://sepolia.basescan.org/tx/0xe12f6de898f9ffe69f7c900853cf792d80c8e15f6a8aef0c766043de04de3ce8) | [`0x92b4d5…`](https://lasna.reactscan.net/tx/0x92b4d5252776e5f395a760a46090a847b254f70658711b03bd01dd0ce3670eb0) | [`0x92b4d5…`](https://lasna.reactscan.net/tx/0x92b4d5252776e5f395a760a46090a847b254f70658711b03bd01dd0ce3670eb0) |
| 30 | no_trade | [`0x7a0ef6…`](https://lasna.reactscan.net/tx/0x7a0ef62e3f8304c3c54aaf58c25dd0b733e87eeaeff7878c000f959e26e7875d) | [`0xa16b1c…`](https://sepolia.basescan.org/tx/0xa16b1cb62bf4b881d58f538e16d01040b0af6815a581638a4768344cef859b2a) | [`0xc046fa…`](https://sepolia.basescan.org/tx/0xc046fa60db2089768d612fdd8f1cb86dcd7d343a115fa283781240981015db25) | [`0x7aa574…`](https://lasna.reactscan.net/tx/0x7aa5745e9b69591f6e17a4c32aada5af52a6b6451f6fe2a4d6d4675714783b18) | [`0x7aa574…`](https://lasna.reactscan.net/tx/0x7aa5745e9b69591f6e17a4c32aada5af52a6b6451f6fe2a4d6d4675714783b18) |
| 31 | no_trade | [`0x964b8f…`](https://lasna.reactscan.net/tx/0x964b8f8a23d25afd291f2b257a7b8f991ad1fa7e40995a970ef1218bf0e8e5cf) | [`0x6ec7b6…`](https://sepolia.basescan.org/tx/0x6ec7b66be2f03ab62d374fa2be283a691a409fb7f27fe8aa8789a15a320a3725) | [`0x1bb40f…`](https://sepolia.basescan.org/tx/0x1bb40fddbfbe7ae02c155e925dd2dd986b5ef95b36dc017c78f4f0c3edbbe205) | [`0x454f2a…`](https://lasna.reactscan.net/tx/0x454f2a55c2439ddfc0bafa70e4dae80ef46d60e0219d51cc5ef1cbc91dc50433) | [`0x454f2a…`](https://lasna.reactscan.net/tx/0x454f2a55c2439ddfc0bafa70e4dae80ef46d60e0219d51cc5ef1cbc91dc50433) |
| 32 | no_trade | [`0x8fdc6b…`](https://lasna.reactscan.net/tx/0x8fdc6b76c12c56a0b071273f537c39fbdedbc30e47dd81d49116f44ea21a55a9) | [`0xda4a23…`](https://sepolia.basescan.org/tx/0xda4a234e8dcf0ec3fabc21e671128d6115a2bedae291f19902611fe41d788ace) | [`0x7eae08…`](https://sepolia.basescan.org/tx/0x7eae081cdc1fd85115475f74ff859bee3f2ade361876406435cfc05389a6f987) | [`0xd6d2c6…`](https://lasna.reactscan.net/tx/0xd6d2c6540d23ef1a3ff421d950c22123071a00af8a30bb3c53e655fbc611243c) | [`0xd6d2c6…`](https://lasna.reactscan.net/tx/0xd6d2c6540d23ef1a3ff421d950c22123071a00af8a30bb3c53e655fbc611243c) |
| 33 | no_trade | [`0x76e9bc…`](https://lasna.reactscan.net/tx/0x76e9bc96b400de8d053bd314ad4269bb42cc53b15cba0c7612fbf8973720a3b8) | [`0xa62be5…`](https://sepolia.basescan.org/tx/0xa62be50e7887c04bf027af1883433112230dc49bd43ffaf062b289b9bce8f406) | [`0x795922…`](https://sepolia.basescan.org/tx/0x795922bcc5d022c5ea5f5cfb0a220246c6e03577349fa68febcf7713081ffd8d) | [`0x0e344d…`](https://lasna.reactscan.net/tx/0x0e344da0efa75d5fc87f0bc1e51fd7b622a3f4206827c9e66018abaf4fa355f9) | [`0x0e344d…`](https://lasna.reactscan.net/tx/0x0e344da0efa75d5fc87f0bc1e51fd7b622a3f4206827c9e66018abaf4fa355f9) |
| 34 | no_trade | [`0x26180c…`](https://lasna.reactscan.net/tx/0x26180c64bad7a2ba6ddeeca34680dcdb183df23443b4e23940c5aba7cd3f5efe) | [`0x1c3ff0…`](https://sepolia.basescan.org/tx/0x1c3ff068a6249693420d17e16bf141d9c5793c345dddab9ddc31cfe9bcc02c94) | [`0xa1d4ac…`](https://sepolia.basescan.org/tx/0xa1d4ac8bbaa0d5bd4859c99e04a75b5fb84953b1dc27a8c4851cc215404e8195) | [`0x6f424a…`](https://lasna.reactscan.net/tx/0x6f424ad21fd34e83d9e83f4753052b9f0457b2f51ed8a7cda69a5e938fe27d0e) | [`0x6f424a…`](https://lasna.reactscan.net/tx/0x6f424ad21fd34e83d9e83f4753052b9f0457b2f51ed8a7cda69a5e938fe27d0e) |
| 35 | no_trade | [`0xebac9b…`](https://lasna.reactscan.net/tx/0xebac9b1281ba776c77a5a80a6215b929303fea4f6fcf218116e302c4e50223c2) | [`0xb5bd47…`](https://sepolia.basescan.org/tx/0xb5bd472307175635d9482ab2acabb1994fbffae31e30a03ccd943c1fa86636e1) | [`0xe7bea2…`](https://sepolia.basescan.org/tx/0xe7bea283303b826ecc87405bacf209ee8d144daa81c2ad03078b2f8e4ab233f0) | [`0x6e623b…`](https://lasna.reactscan.net/tx/0x6e623b1b8266d5169681677d8dc1c0820e30dd91bfe9350fc7f354965602fc1c) | [`0x6e623b…`](https://lasna.reactscan.net/tx/0x6e623b1b8266d5169681677d8dc1c0820e30dd91bfe9350fc7f354965602fc1c) |
| 36 | no_trade | [`0x6b0876…`](https://lasna.reactscan.net/tx/0x6b087644f0b6c8de038e4f9a548ca189f1d70842f8d3da89b6dabafe9809aaa7) | [`0x59e801…`](https://sepolia.basescan.org/tx/0x59e80169e7d02b7f23029b4ca7c156cdbbd83747cb51be7009a7a95ecfe2c8fe) | [`0xf651a0…`](https://sepolia.basescan.org/tx/0xf651a09c92d94c85fed4a2411444bcd427d12efaa6a8702f8fb5f5e45752e9a0) | [`0xbf0077…`](https://lasna.reactscan.net/tx/0xbf0077bb6f5f9b4cdd9308fa693bdfe9baa21822bc905bde5afec637bed69c3f) | [`0xbf0077…`](https://lasna.reactscan.net/tx/0xbf0077bb6f5f9b4cdd9308fa693bdfe9baa21822bc905bde5afec637bed69c3f) |
| 37 | rebalanced | [`0xd546d4…`](https://lasna.reactscan.net/tx/0xd546d45568977025a7bd60e6695871f923e3a1a33623559354babfb2832c3908) | [`0x889d09…`](https://sepolia.basescan.org/tx/0x889d0946911861b7f53fcb29144b4a982fa1264ddf3cabae45488a9c632a33ba) | [`0x13fe39…`](https://sepolia.basescan.org/tx/0x13fe3944decb8580753b90934be077e946b6de775e3a9b1218d29b7ee52d9d3f) | [`0x0d2845…`](https://lasna.reactscan.net/tx/0x0d2845aa3c3dd6e30863c29f836871d72e65813bc4974d741893a949912d6e58) | [`0x6c23b7…`](https://sepolia.basescan.org/tx/0x6c23b7fda15cdb86f27d99ccc6572c48cdc8c3af4d792f4638feab909ba2a1d8) |
| 38 | no_trade | [`0x42aa67…`](https://lasna.reactscan.net/tx/0x42aa676d6d375f6a3a6adb723ca2bd15a8d87ea4e6f227dc837c061689c3ba94) | [`0x0f6fa6…`](https://sepolia.basescan.org/tx/0x0f6fa6c8c25083c9e1ddab6a5c6f53123cfd37eca61391ddb70b92f9ad85e576) | [`0x9c7104…`](https://sepolia.basescan.org/tx/0x9c710488ebfd4618f1e45cd1db8caaab76f895700efbcfecd6e46d4f1557a3f1) | [`0xec82a5…`](https://lasna.reactscan.net/tx/0xec82a50ce78152d420e8008389dac8823011550569f7cd16c53a57c66701a013) | [`0xec82a5…`](https://lasna.reactscan.net/tx/0xec82a50ce78152d420e8008389dac8823011550569f7cd16c53a57c66701a013) |
| 39 | no_trade | [`0x15c8d9…`](https://lasna.reactscan.net/tx/0x15c8d9091ed4cb6f67b0a3af884c62261f219f596dafccb17ae2f4cd55d0009b) | [`0x2e2309…`](https://sepolia.basescan.org/tx/0x2e23090803c1c1d48f0312fa1c6040d5987b06dde832f77be5d023ccface9d58) | [`0xb28e92…`](https://sepolia.basescan.org/tx/0xb28e9224e243cf2a17c996f905e6d5e96cb67d4a48927c56eb3459e8e23ade60) | [`0xf716dc…`](https://lasna.reactscan.net/tx/0xf716dcfe11ec2e5994af522a1987246f61dc989d48b9faab3c514ebb5f54e8f1) | [`0xf716dc…`](https://lasna.reactscan.net/tx/0xf716dcfe11ec2e5994af522a1987246f61dc989d48b9faab3c514ebb5f54e8f1) |
| 40 | no_trade | [`0x40032b…`](https://lasna.reactscan.net/tx/0x40032b38bffecbcdb1fc289cb6ec245c37e43b11ac0614b44f71108b60412938) | [`0xdeef42…`](https://sepolia.basescan.org/tx/0xdeef422406b9a28aa5837f718aa63b3cb37810b82f0219c01f2e004ed79c76d9) | [`0xd58c67…`](https://sepolia.basescan.org/tx/0xd58c6770b0d525922bf5553746ffe266d4664db0ee85bf699a7cf400e70f3b68) | [`0x0cb25b…`](https://lasna.reactscan.net/tx/0x0cb25b833db2479b5d44d64dc15cc7dae5a3e8b427c7cc69fe4bde46ec52baf2) | [`0x0cb25b…`](https://lasna.reactscan.net/tx/0x0cb25b833db2479b5d44d64dc15cc7dae5a3e8b427c7cc69fe4bde46ec52baf2) |
| 41 | no_trade | [`0xdcaa40…`](https://lasna.reactscan.net/tx/0xdcaa408d14e97d0357753af93a7825af5f22b719c7ab973a8c1783055d569f0c) | [`0xa59097…`](https://sepolia.basescan.org/tx/0xa59097fcc34228f86776e58389bae6f017d63c522081cf17cf9476fec3a51ab2) | [`0xb88bc5…`](https://sepolia.basescan.org/tx/0xb88bc55174ff7d63074f0bd1c9f5564d2c96b9bd362834ffa77854c5c37b2bdf) | [`0xbccd17…`](https://lasna.reactscan.net/tx/0xbccd17ec7217be26d8199a7403fa7436bc75371377acaec0c916a8b782beb95c) | [`0xbccd17…`](https://lasna.reactscan.net/tx/0xbccd17ec7217be26d8199a7403fa7436bc75371377acaec0c916a8b782beb95c) |
| 42 | no_trade | [`0x140e83…`](https://lasna.reactscan.net/tx/0x140e836f7ee48e31ce621e1810e4c07bb05fad9d474047b8024c9b6cfd309043) | [`0xe5a67d…`](https://sepolia.basescan.org/tx/0xe5a67dce3c7f27d04037147938e7f0b266757d7279870338f37b76babac4c7b8) | [`0x47022d…`](https://sepolia.basescan.org/tx/0x47022d947f1b57dcc755073f923ed874d6240295ead01ff8e3e8008423055f7c) | [`0x3fa495…`](https://lasna.reactscan.net/tx/0x3fa495a597f912b8c37bb975b6d380d900f7be40592003d6b145119ee2b495b8) | [`0x3fa495…`](https://lasna.reactscan.net/tx/0x3fa495a597f912b8c37bb975b6d380d900f7be40592003d6b145119ee2b495b8) |
| 43 | no_trade | [`0x262286…`](https://lasna.reactscan.net/tx/0x2622861beb89b468b7401f90fca9c5a29567989fa1a7e8628d7877a8929a8050) | [`0x2e0d78…`](https://sepolia.basescan.org/tx/0x2e0d78adb31bba39b2dca1db0fdda825ee4976909ef8313cee1e8500a27d77be) | [`0x1f31bd…`](https://sepolia.basescan.org/tx/0x1f31bd5395722730fd53f528c3dc42e4dfaa2d6e56cdf3484814668987df2425) | [`0x5be31e…`](https://lasna.reactscan.net/tx/0x5be31e0a330b53ecdb4072466051ace2e3bb042f02b3da5ca7712f43941792e7) | [`0x5be31e…`](https://lasna.reactscan.net/tx/0x5be31e0a330b53ecdb4072466051ace2e3bb042f02b3da5ca7712f43941792e7) |
| 44 | no_trade | [`0x1fb730…`](https://lasna.reactscan.net/tx/0x1fb730bb9b5eac45ab4d97e1971739f5878844728ce818dc1d4a7d430a6c96d7) | [`0xb79d6f…`](https://sepolia.basescan.org/tx/0xb79d6f810e50ffee285fcb718b824d16ab7f6fd16df98a891ae4ca416de7053a) | [`0xc5e726…`](https://sepolia.basescan.org/tx/0xc5e726e97344662cbc42c8bd4b55a81c8cbea5e9a82b882cc2d54645e018b8d5) | [`0x9b3b34…`](https://lasna.reactscan.net/tx/0x9b3b34829156d00968175adac88455ed3be50bdec28455b963284879615412b1) | [`0x9b3b34…`](https://lasna.reactscan.net/tx/0x9b3b34829156d00968175adac88455ed3be50bdec28455b963284879615412b1) |
| 45 | no_trade | [`0x853603…`](https://lasna.reactscan.net/tx/0x853603c04a46e950638ca9780a59931418cefb864602c007a94c0eed0ac5ab33) | [`0xb89ff4…`](https://sepolia.basescan.org/tx/0xb89ff4aa66c27a4a3203d765c1699138d9f7a8f35183dda83b18edfc53a42b69) | [`0xcd678d…`](https://sepolia.basescan.org/tx/0xcd678d82537f720d8edaf6906042c26f9dde0af3865b9f81eb7e7ebf34755520) | [`0xcaf7af…`](https://lasna.reactscan.net/tx/0xcaf7afbdd893a8f98d83af9756e93eef411e76ae061dbd3ba007fd94caafa9be) | [`0xcaf7af…`](https://lasna.reactscan.net/tx/0xcaf7afbdd893a8f98d83af9756e93eef411e76ae061dbd3ba007fd94caafa9be) |
| 46 | no_trade | [`0x0a8b33…`](https://lasna.reactscan.net/tx/0x0a8b33ff22843ec3c0cae099a2b3ba15c8da9ab0eb81c441847ba883740d1630) | [`0xb581b8…`](https://sepolia.basescan.org/tx/0xb581b828bfa36e2ad48994bfdaac80cb42432fce2eef6bb0463264adcaf2e6a1) | [`0x4d0741…`](https://sepolia.basescan.org/tx/0x4d0741d48188812abd3041d47668cecead22e612c7e427ca72560dbe2010583d) | [`0x6fe235…`](https://lasna.reactscan.net/tx/0x6fe2352b78b332c81b728604a6c7bb312c7f0cd0625daf84500568762e1448fb) | [`0x6fe235…`](https://lasna.reactscan.net/tx/0x6fe2352b78b332c81b728604a6c7bb312c7f0cd0625daf84500568762e1448fb) |
| 47 | no_trade | [`0x27d3d7…`](https://lasna.reactscan.net/tx/0x27d3d7d2a4e7a49c82137d74206d5675015f23c3804c38178e7a924295f64190) | [`0x9767a6…`](https://sepolia.basescan.org/tx/0x9767a6d4dbdfe375e30f57f4606d49cd162881f659e408197457c71653aa6124) | [`0x319195…`](https://sepolia.basescan.org/tx/0x3191957613b23135fc2d184caa77d27ed5241c4aaffc98a77f182a4a77f8f722) | [`0x1843b7…`](https://lasna.reactscan.net/tx/0x1843b72918002b2c08d7b7be239b6ebd0264563262fca06fabb47318d45e4959) | [`0x1843b7…`](https://lasna.reactscan.net/tx/0x1843b72918002b2c08d7b7be239b6ebd0264563262fca06fabb47318d45e4959) |
| 48 | no_trade | [`0x014260…`](https://lasna.reactscan.net/tx/0x014260404a1f0623bcebbd68eda88d4f52ef91b48a85d4f425ca1dfe765a12c3) | [`0xbbb998…`](https://sepolia.basescan.org/tx/0xbbb9980d4d10954a27a13cf3ec9818510b957a7863c2e1b22981c822ffb3e631) | [`0x54c3d1…`](https://sepolia.basescan.org/tx/0x54c3d165c058b38a59cb4e1863423fdef2250718a0bd276dfff4d4f9c84563a6) | [`0x54e3ba…`](https://lasna.reactscan.net/tx/0x54e3ba38092a3ed58ee080d915853e2212ba8e11fff15c095f70a5c08624f21d) | [`0x54e3ba…`](https://lasna.reactscan.net/tx/0x54e3ba38092a3ed58ee080d915853e2212ba8e11fff15c095f70a5c08624f21d) |
| 49 | no_trade | [`0x7dbe7c…`](https://lasna.reactscan.net/tx/0x7dbe7c2e1bbf90c6f85366ce5affe8369d91987f3b6c5c0031ac65439c525710) | [`0xfda12e…`](https://sepolia.basescan.org/tx/0xfda12e4f064b376cca8dc1a60b4a74627338f2d5b7518fce98052b00c4bab368) | [`0x4734ba…`](https://sepolia.basescan.org/tx/0x4734baf5655947c4984c96557189d0add103bd0591931d0706bbe9a07cbc48d3) | [`0xcdec5d…`](https://lasna.reactscan.net/tx/0xcdec5de88b4405f6a86f5564facdae4f41c1be8e0ee9f4d26741f936c0f322d9) | [`0xcdec5d…`](https://lasna.reactscan.net/tx/0xcdec5de88b4405f6a86f5564facdae4f41c1be8e0ee9f4d26741f936c0f322d9) |
| 50 | no_trade | [`0x3adc4f…`](https://lasna.reactscan.net/tx/0x3adc4fa577726e2f80885f08ae8c8aaacac1ddadda8e8721cd76f11301b28be9) | [`0x404556…`](https://sepolia.basescan.org/tx/0x40455676f0bf61dd1a74b8f1749d0ee417a962ef1c043a10da695ecf5457d51d) | [`0x4f66f5…`](https://sepolia.basescan.org/tx/0x4f66f5493e020b0017615aeaee928293244aa56559258e1c98e0a42f07f7eec6) | [`0x864b86…`](https://lasna.reactscan.net/tx/0x864b867625fe9db65e16e084adf06c00dde5ee8a31ecdeaa71451f61a9a7a633) | [`0x864b86…`](https://lasna.reactscan.net/tx/0x864b867625fe9db65e16e084adf06c00dde5ee8a31ecdeaa71451f61a9a7a633) |
| 51 | no_trade | [`0x01aa93…`](https://lasna.reactscan.net/tx/0x01aa93183f678db7b245f48e6a1e3eea73f4cc048028891a5900ece85f04ab32) | [`0xcfad1c…`](https://sepolia.basescan.org/tx/0xcfad1cc47679add21b8094be17e79a36b00e50d08f8c82b03dce4c102457418b) | [`0xa36382…`](https://sepolia.basescan.org/tx/0xa3638285baf68b217e38b07ba511a1c6801f99e170c1ac82733204834de865ac) | [`0x5b6957…`](https://lasna.reactscan.net/tx/0x5b6957bd36e1114d9d0873c785a366dcf998e2d49081dd0cd18ad67b946807f3) | [`0x5b6957…`](https://lasna.reactscan.net/tx/0x5b6957bd36e1114d9d0873c785a366dcf998e2d49081dd0cd18ad67b946807f3) |
| 52 | no_trade | [`0x497e07…`](https://lasna.reactscan.net/tx/0x497e07061f62c1c40a23d95e16bb48f6b920e6ae2104c0599732e47c2755da2e) | [`0xd2bd5b…`](https://sepolia.basescan.org/tx/0xd2bd5b405ff76c101196836c4cce6c395763d1f4afd6a6ddfea6398a7c57147c) | [`0x0ab2c7…`](https://sepolia.basescan.org/tx/0x0ab2c7be9408cf4f0469c4266e32aaba129e94228444589c277ecfb195a0fa4e) | [`0xbe156a…`](https://lasna.reactscan.net/tx/0xbe156a86bb14cb5bd856fb52f08fe86c3001316214d4e5d0238aa819047a89d6) | [`0xbe156a…`](https://lasna.reactscan.net/tx/0xbe156a86bb14cb5bd856fb52f08fe86c3001316214d4e5d0238aa819047a89d6) |
| 53 | no_trade | [`0x89375e…`](https://lasna.reactscan.net/tx/0x89375e99f088f236c4b61cb01d12155c2e73231073627bdaba5d656b03b5ae9a) | [`0x22b023…`](https://sepolia.basescan.org/tx/0x22b0236b515f1ff1f1383ea8828a93d17ccff51be3ba1cd92dca9c24bbe6428e) | [`0x5ad739…`](https://sepolia.basescan.org/tx/0x5ad739dbbdd70f35238bda1d947e82bf6dd3fbff942ff85053d6958fe77d25e8) | [`0x42fb26…`](https://lasna.reactscan.net/tx/0x42fb26a9a666ae4b9d7d0e4070ee767d88afecadb61f636ffd47bc252ac7cf23) | [`0x42fb26…`](https://lasna.reactscan.net/tx/0x42fb26a9a666ae4b9d7d0e4070ee767d88afecadb61f636ffd47bc252ac7cf23) |
| 54 | no_trade | [`0xf12904…`](https://lasna.reactscan.net/tx/0xf1290499eccf3f96431f97557071edbe2bea7aeadf31e5ea81617ae84d307594) | [`0x744c4a…`](https://sepolia.basescan.org/tx/0x744c4aba642492229c5d86b528e261a3f78bbb31aed7e7c0ae6a063161c6a9fc) | [`0x305b9f…`](https://sepolia.basescan.org/tx/0x305b9ff5a16285a93dcbee8c0ad38ef033f294a9f03b74b7fab7adc3a15bb9c1) | [`0x86f31f…`](https://lasna.reactscan.net/tx/0x86f31f42298cbd013d17cc035cc9da44d852e9a21a8caf39a8a512527e319c01) | [`0x86f31f…`](https://lasna.reactscan.net/tx/0x86f31f42298cbd013d17cc035cc9da44d852e9a21a8caf39a8a512527e319c01) |
| 55 | no_trade | [`0x6931d6…`](https://lasna.reactscan.net/tx/0x6931d689554396ddf7c1018a32bd5844bd1c33eeb5f564b0ef7e50cb62492b0a) | [`0x74087a…`](https://sepolia.basescan.org/tx/0x74087a0a67b05440dd416449b31df13a32298c83d612cf35b4fd2da535a95647) | [`0x418cab…`](https://sepolia.basescan.org/tx/0x418cabddd1de297c6f506f271942dc5ceac851add3ad97bbbb8ed2af30b22861) | [`0x5ff59f…`](https://lasna.reactscan.net/tx/0x5ff59f0b48f9ca499fcaf373aad9f0ac60c8455e8aff66cd98dff9679958b399) | [`0x5ff59f…`](https://lasna.reactscan.net/tx/0x5ff59f0b48f9ca499fcaf373aad9f0ac60c8455e8aff66cd98dff9679958b399) |
| 56 | no_trade | [`0x824f80…`](https://lasna.reactscan.net/tx/0x824f803cbdcf26f153451a31ac5e4e191799b89879ebbfc3efc0e09114c4b714) | [`0xf54cac…`](https://sepolia.basescan.org/tx/0xf54caca9fbbf1b443d37901966c9d5dd38742d233d8fa4f7eb247d3501736201) | [`0xcedc3c…`](https://sepolia.basescan.org/tx/0xcedc3cba6eef4cb122556d15c874c58c40a9e747c3565c1c7dfce9f8ba0d87b7) | [`0xb37d26…`](https://lasna.reactscan.net/tx/0xb37d2639439df06a704ef6e8adf2f2c6ccd75fec7e6bfc0973561526c0cc373a) | [`0xb37d26…`](https://lasna.reactscan.net/tx/0xb37d2639439df06a704ef6e8adf2f2c6ccd75fec7e6bfc0973561526c0cc373a) |
| 57 | no_trade | [`0x377a43…`](https://lasna.reactscan.net/tx/0x377a43d85b85fe1eaa022efc2f6fde92582753ea4b4b5ae29b7ae691bbc21e99) | [`0x1f7ba9…`](https://sepolia.basescan.org/tx/0x1f7ba94ebe3d8e8f8a3a90dc64b389490cb6736d00027aaf5480ed57751d2dbb) | [`0x3deefb…`](https://sepolia.basescan.org/tx/0x3deefbb4b5e0afd5b50d788f451591e5ae7dcca10d2acf023366b447d6643dc1) | [`0xe5015c…`](https://lasna.reactscan.net/tx/0xe5015ccf58985599fac6e073f15eb451acbb00bb6ec536ca71d2053eb260d0e9) | [`0xe5015c…`](https://lasna.reactscan.net/tx/0xe5015ccf58985599fac6e073f15eb451acbb00bb6ec536ca71d2053eb260d0e9) |
| 58 | no_trade | [`0xd8478f…`](https://lasna.reactscan.net/tx/0xd8478fc1bd70437dc01639e2b3fdc5c2deed96ae4cd9ca292dd7d174ec06f372) | [`0x3586d5…`](https://sepolia.basescan.org/tx/0x3586d50dc0e969fcbd035e2a6c6e0fffd7ce1cb6fc7df4bd1de350508471ea0d) | [`0x4f7e30…`](https://sepolia.basescan.org/tx/0x4f7e308c12e4cc627261901a40d586498484d4d34358dc22f4a9779abefaf8c2) | [`0xcdd349…`](https://lasna.reactscan.net/tx/0xcdd349fe4eb94ef6f5f04db7ec3f4788ab90749f3020509b26372c50211ecfea) | [`0xcdd349…`](https://lasna.reactscan.net/tx/0xcdd349fe4eb94ef6f5f04db7ec3f4788ab90749f3020509b26372c50211ecfea) |
| 59 | no_trade | [`0xd77259…`](https://lasna.reactscan.net/tx/0xd77259b7ca8c9f1bbcecba37e567727d20a765f9f3fa87a24f30cddf7947a548) | [`0x81148b…`](https://sepolia.basescan.org/tx/0x81148b3a2aa935c2f35f52fd97062b7c5264194a7dc8488ebd3d9723723d1054) | [`0x326ef8…`](https://sepolia.basescan.org/tx/0x326ef8800c4c3304090ad21ef34ba687710c4b56c42aa8e3eaa33029cfdbd696) | [`0x91a039…`](https://lasna.reactscan.net/tx/0x91a03911052be26ac821764735e02622249c7504d6e42341369b10a6650d2cfa) | [`0x91a039…`](https://lasna.reactscan.net/tx/0x91a03911052be26ac821764735e02622249c7504d6e42341369b10a6650d2cfa) |
| 60 | no_trade | [`0xf85879…`](https://lasna.reactscan.net/tx/0xf85879fc89b55e1000b2cb775542064de088bc1614af0ecf37407280387f0107) | [`0x6cbc01…`](https://sepolia.basescan.org/tx/0x6cbc019cae3430c88fdc4fdbb9d93924c568edac444227a6715e2523eb442351) | [`0x24de7e…`](https://sepolia.basescan.org/tx/0x24de7e9c83342e93976764720466b0a69cae33951dceaf8fb621b00787c5960b) | [`0x4672bc…`](https://lasna.reactscan.net/tx/0x4672bc4da578a85b45855c041c3a5c11e0a64c3ca8e57ca56e9de37f9eae4e5f) | [`0x4672bc…`](https://lasna.reactscan.net/tx/0x4672bc4da578a85b45855c041c3a5c11e0a64c3ca8e57ca56e9de37f9eae4e5f) |
| 61 | no_trade | [`0x63171a…`](https://lasna.reactscan.net/tx/0x63171ac4824edace8e2497b2b8ed17c3304ec608aa5ec174cd9f633345f40b9e) | [`0x15ca41…`](https://sepolia.basescan.org/tx/0x15ca4138a224f4fdad9f422deaf7fbce2fc41b595f3526aea8480bfa2f16535e) | [`0xa4b91f…`](https://sepolia.basescan.org/tx/0xa4b91f6381e0d8d8db6fed7c29e85c82b9c876ccaa08a45dd42353e4cc65a696) | [`0x76c052…`](https://lasna.reactscan.net/tx/0x76c052dcc11eccfda620e1358a15caa1e8ebecd15ab6e931172fa129befd6cf2) | [`0x76c052…`](https://lasna.reactscan.net/tx/0x76c052dcc11eccfda620e1358a15caa1e8ebecd15ab6e931172fa129befd6cf2) |
| 62 | no_trade | [`0xb8d532…`](https://lasna.reactscan.net/tx/0xb8d532e4b3cc9b5610714872fee1d058c28e3e940b146273ec41a9b3ce8d9bab) | [`0x515d37…`](https://sepolia.basescan.org/tx/0x515d37c3d82ce79034410b9bfb6fa53cf75d95ee98ef055f717ca7ba19130212) | [`0x447866…`](https://sepolia.basescan.org/tx/0x44786669df8b47c974b01073343d9797a8cc27d5ca8cd7fbecb2fa04ab4586e4) | [`0x1989cd…`](https://lasna.reactscan.net/tx/0x1989cd93aa099157f2f07e602dc3399a01c131ff161d9a9685eaa84681a76159) | [`0x1989cd…`](https://lasna.reactscan.net/tx/0x1989cd93aa099157f2f07e602dc3399a01c131ff161d9a9685eaa84681a76159) |
| 63 | no_trade | [`0x9d63d4…`](https://lasna.reactscan.net/tx/0x9d63d497c168f090ec9990ea4fba0322905afc75154ede595c2c4876de4f0a24) | [`0xc2faba…`](https://sepolia.basescan.org/tx/0xc2faba85f984eda93abae936c32aaddae78031fed866aa43c68b863753dd8820) | [`0xb3f477…`](https://sepolia.basescan.org/tx/0xb3f477e90ef7133668fc001d5a820f99ae6a8e7d0723fa0fcdac34186731359c) | [`0x12c7b8…`](https://lasna.reactscan.net/tx/0x12c7b898efea0c3fc41820b0887c2f7c37e02c75180d0cde9c18039e996869b2) | [`0x12c7b8…`](https://lasna.reactscan.net/tx/0x12c7b898efea0c3fc41820b0887c2f7c37e02c75180d0cde9c18039e996869b2) |
| 64 | no_trade | [`0x455b46…`](https://lasna.reactscan.net/tx/0x455b46363838de0025ef6a882de9d4def80f5c8e068e956bc9ec9a04eda0bf4c) | [`0x6c9b0a…`](https://sepolia.basescan.org/tx/0x6c9b0ae68dc1a49bb971a0b32b86fc4b84984e9eb7ae40f0a8a6e11f0a96f27f) | [`0xe06365…`](https://sepolia.basescan.org/tx/0xe06365bd0357f946f5b3946ae3d288d0a310b9228847b77d71ad2b0467ab65ee) | [`0x20b11c…`](https://lasna.reactscan.net/tx/0x20b11c63578ebb0efe17c0e690b2ca29afea75171348540fb6509f3b75cd0c9d) | [`0x20b11c…`](https://lasna.reactscan.net/tx/0x20b11c63578ebb0efe17c0e690b2ca29afea75171348540fb6509f3b75cd0c9d) |
| 65 | no_trade | [`0x94642d…`](https://lasna.reactscan.net/tx/0x94642d44f63bfd395f5f037326562bb24cfdbd32c8e1dce83cf6ca756eb48be7) | [`0xda41a0…`](https://sepolia.basescan.org/tx/0xda41a0a7bf27432fbfc26a885ac43c66753042760fc26d540317119dc970fc24) | [`0x89ee85…`](https://sepolia.basescan.org/tx/0x89ee858fe8ca397ce914659e46408431ec29a8214f4cb0bc33abe2d8946778b4) | [`0x5430ab…`](https://lasna.reactscan.net/tx/0x5430ab79ae2692d8b11bf8020f287fb8246dbf6041d7fe1276b98d4eb7a7333c) | [`0x5430ab…`](https://lasna.reactscan.net/tx/0x5430ab79ae2692d8b11bf8020f287fb8246dbf6041d7fe1276b98d4eb7a7333c) |
| 66 | expired | [`0xda6adf…`](https://lasna.reactscan.net/tx/0xda6adf4c3cd722345232fd6fffe253d9b09d9e2c8404dc9b376d62ea28437765) | [`0x1699f3…`](https://sepolia.basescan.org/tx/0x1699f36de9b5a67f347dcfc6f022ff1b54e43f4b43b48c64a3ffb39c7427619a) | — | — | [`0x761401…`](https://lasna.reactscan.net/tx/0x76140115760d31932a5c17d888cd952bdc9e28fa8d5aaa88a91a27d1abdd70db) |
| 67 | expired | [`0x761401…`](https://lasna.reactscan.net/tx/0x76140115760d31932a5c17d888cd952bdc9e28fa8d5aaa88a91a27d1abdd70db) | [`0x22ba6c…`](https://sepolia.basescan.org/tx/0x22ba6c6db6482e55225c5e4ed9799091d53df86e62ee78f99c18b955c6396329) | — | — | [`0x7a54a4…`](https://lasna.reactscan.net/tx/0x7a54a4ab1cba41d84b037986c467dc0638b6b5479c4acfad9f91c8183030f08b) |
| 68 | expired | [`0x7a54a4…`](https://lasna.reactscan.net/tx/0x7a54a4ab1cba41d84b037986c467dc0638b6b5479c4acfad9f91c8183030f08b) | [`0xc4aecc…`](https://sepolia.basescan.org/tx/0xc4aecc15f0ee9dca728182a16b87be2a4ef247bb19f4e2563e27899535bc683d) | — | — | [`0x213022…`](https://lasna.reactscan.net/tx/0x213022b7ed1062f1cd89b84e31d188b5f68faa728d81c8ff0b9995f282a4a1e1) |
| 69 | expired | [`0x213022…`](https://lasna.reactscan.net/tx/0x213022b7ed1062f1cd89b84e31d188b5f68faa728d81c8ff0b9995f282a4a1e1) | [`0xd1b25c…`](https://sepolia.basescan.org/tx/0xd1b25cc7c60b3ccc488ea4cc717ada07afd7d4b31677f2fdd394bdf0426063d9) | — | — | [`0x7bffcd…`](https://lasna.reactscan.net/tx/0x7bffcdf5fea708c958f6d0b2ec107b4fa62d3699c66a9315e9248c5a91023556) |
| 70 | expired | [`0x7bffcd…`](https://lasna.reactscan.net/tx/0x7bffcdf5fea708c958f6d0b2ec107b4fa62d3699c66a9315e9248c5a91023556) | [`0xc9e65b…`](https://sepolia.basescan.org/tx/0xc9e65b20cf21e89c065e358d746f37d63d866e30999f3c005b95629093fabf99) | — | — | [`0xb8780d…`](https://lasna.reactscan.net/tx/0xb8780d2c676e905c2f5ab1f8eda283fbb0d67a360f695bee2fd16ec03b18a2fa) |
| 71 | expired | [`0xb8780d…`](https://lasna.reactscan.net/tx/0xb8780d2c676e905c2f5ab1f8eda283fbb0d67a360f695bee2fd16ec03b18a2fa) | [`0xdfefc5…`](https://sepolia.basescan.org/tx/0xdfefc5898c23ff15741e3d6a44ea8779496cf25d20bab7481d8959d6785af694) | — | — | [`0xbc7c99…`](https://lasna.reactscan.net/tx/0xbc7c994541aba2eb44596dc12bafeff05297e6dc08b8eaad8a20b804d49a2734) |
| 72 | expired | [`0xbc7c99…`](https://lasna.reactscan.net/tx/0xbc7c994541aba2eb44596dc12bafeff05297e6dc08b8eaad8a20b804d49a2734) | [`0x05545c…`](https://sepolia.basescan.org/tx/0x05545c1c54bb05a4ea0759d6aa8e00b052dd60e6b6629abfd23d62c02c3af8b3) | — | — | [`0xb10e8d…`](https://lasna.reactscan.net/tx/0xb10e8dc91cbaefa25298d0641516fd34ad91dcc8a9d7edef4466b6adb7d8141e) |
| 73 | expired | [`0xb10e8d…`](https://lasna.reactscan.net/tx/0xb10e8dc91cbaefa25298d0641516fd34ad91dcc8a9d7edef4466b6adb7d8141e) | [`0xa430f2…`](https://sepolia.basescan.org/tx/0xa430f2b0e05ab3f4743e0e0caee6aafa6a05bd3d9edb9f48ae80e80f5cb3eb4a) | — | — | [`0x84084b…`](https://lasna.reactscan.net/tx/0x84084b20b9f01eb83b22782ff1899c947398a12727997b5ef1261a301f9cd9db) |
| 74 | expired | [`0x84084b…`](https://lasna.reactscan.net/tx/0x84084b20b9f01eb83b22782ff1899c947398a12727997b5ef1261a301f9cd9db) | [`0x4c8f70…`](https://sepolia.basescan.org/tx/0x4c8f702d897cdf9a556705874b2fadc2ea3e6ebf5c82b27043f128dcb4c068dc) | — | — | [`0x1bec47…`](https://lasna.reactscan.net/tx/0x1bec47d3e162b63fcef58882b915076c1e6b24b41e293ff9a20e24e5ee12abe4) |
| 75 | expired | [`0x1bec47…`](https://lasna.reactscan.net/tx/0x1bec47d3e162b63fcef58882b915076c1e6b24b41e293ff9a20e24e5ee12abe4) | [`0x0d4fc5…`](https://sepolia.basescan.org/tx/0x0d4fc59d3a0ad853858223038cb18cd7ecf8b02310641ea609d8948f1b693f9b) | — | — | [`0x6aa2e6…`](https://lasna.reactscan.net/tx/0x6aa2e6e5bbc03eef50a5869bb3c08e30f704ab646de0907970e3a725ed2f6bd4) |
| 76 | no_trade | [`0x6aa2e6…`](https://lasna.reactscan.net/tx/0x6aa2e6e5bbc03eef50a5869bb3c08e30f704ab646de0907970e3a725ed2f6bd4) | [`0xf5b2db…`](https://sepolia.basescan.org/tx/0xf5b2dbf4efbefa0785b3d1074bd5a1624eb5a0c2aef8dd0e9d792378d7d94f08) | [`0xd80d1a…`](https://sepolia.basescan.org/tx/0xd80d1a745c65406d090446fbee18e92fc53a03dd9a8ee9adffc3a168a0290f2a) | [`0x5c9d97…`](https://lasna.reactscan.net/tx/0x5c9d97a141c59b8754d5c0bb333a7c8e2cbd7c3afda045a172a6ea40067715aa) | [`0x5c9d97…`](https://lasna.reactscan.net/tx/0x5c9d97a141c59b8754d5c0bb333a7c8e2cbd7c3afda045a172a6ea40067715aa) |
| 77 | no_trade | [`0xcd74d0…`](https://lasna.reactscan.net/tx/0xcd74d059a102c7278d2c5427660cfa384c459e82b308a774fd3d1950edc812bb) | [`0xe8af46…`](https://sepolia.basescan.org/tx/0xe8af460b5b718d653d6ae47a7b9afce8beee4abe91d065abd63eded44f0b1e6a) | [`0xb0c408…`](https://sepolia.basescan.org/tx/0xb0c408903fea9576a4d226301435f1b3c5f50507e3794b0f1ae47d0571e53299) | [`0x96b0b5…`](https://lasna.reactscan.net/tx/0x96b0b5545136a909d7e6c427a4c8589388b80d5c5cc14ac912747f85ac5463a5) | [`0x96b0b5…`](https://lasna.reactscan.net/tx/0x96b0b5545136a909d7e6c427a4c8589388b80d5c5cc14ac912747f85ac5463a5) |
| 78 | no_trade | [`0xc92a92…`](https://lasna.reactscan.net/tx/0xc92a9280d96ac34433378ca0015517a7aa26ad5b6b155f7d774dfe30f8d4a172) | [`0xfae645…`](https://sepolia.basescan.org/tx/0xfae645dbf6877fbdf50bebcaf6654020ca830f01069c3d203f09bc289d41da61) | [`0xe72e65…`](https://sepolia.basescan.org/tx/0xe72e652822ee95ca379df2be4f83ac4347d68738b49760c6874d3666f36e363a) | [`0xab8fde…`](https://lasna.reactscan.net/tx/0xab8fde9b6f6bf94630ae89e45f96c069bfea588a9389ea1d5422d61991885910) | [`0xab8fde…`](https://lasna.reactscan.net/tx/0xab8fde9b6f6bf94630ae89e45f96c069bfea588a9389ea1d5422d61991885910) |
| 79 | no_trade | [`0xd9e5d2…`](https://lasna.reactscan.net/tx/0xd9e5d2fc01457e17c97ee6d361e5f58cfdb1e15a086575fa8298247a7ef8141c) | [`0x1ca91f…`](https://sepolia.basescan.org/tx/0x1ca91f85dd6705ed8b46d63ca9217f5a763171905b3d81a33b2c54b0efa95e43) | [`0x596f27…`](https://sepolia.basescan.org/tx/0x596f272ef996b1f4f265cc3900c13ffb00d878b6e2520971d0a637075b9144a8) | [`0xf61525…`](https://lasna.reactscan.net/tx/0xf6152559d27e1110d5be28bc672748ffcbbb4e2534790db2c30247f7564b09f3) | [`0xf61525…`](https://lasna.reactscan.net/tx/0xf6152559d27e1110d5be28bc672748ffcbbb4e2534790db2c30247f7564b09f3) |
| 80 | no_trade | [`0x7c53ca…`](https://lasna.reactscan.net/tx/0x7c53ca680104e43a610dd4a652d7614231b8add4fbf443fe166ec8f380a43180) | [`0xff6d3f…`](https://sepolia.basescan.org/tx/0xff6d3f8b7d53140f865db38c2565f09cee599bd1cb37562f35c635bf25840c0a) | [`0x8174f8…`](https://sepolia.basescan.org/tx/0x8174f8e210ec7b205fe9e1c0886d335cb00a88a7bde8b800f0223890f09c60b9) | [`0xaad645…`](https://lasna.reactscan.net/tx/0xaad645062602f52b1d5549b1b6352283deb463bc6309932602e335094c79de07) | [`0xaad645…`](https://lasna.reactscan.net/tx/0xaad645062602f52b1d5549b1b6352283deb463bc6309932602e335094c79de07) |
| 81 | no_trade | [`0xbafb27…`](https://lasna.reactscan.net/tx/0xbafb27e4414ec41ed19c1b77680839b098e4176e2425580e3e9ed611007eb252) | [`0xd52630…`](https://sepolia.basescan.org/tx/0xd52630b2afd12211b5fe3d81d3fde5e57cd31431badb1ce67d6187c66fba85de) | [`0x727797…`](https://sepolia.basescan.org/tx/0x727797abed49903c92fe17936f6dfced473e09dca160cab20396ec3d26c723ca) | [`0x2205be…`](https://lasna.reactscan.net/tx/0x2205be299279614cf0c977bff2ee85290eafd42ff60ba6b10a65fe809438ade1) | [`0x2205be…`](https://lasna.reactscan.net/tx/0x2205be299279614cf0c977bff2ee85290eafd42ff60ba6b10a65fe809438ade1) |
| 82 | no_trade | [`0x0a0d6b…`](https://lasna.reactscan.net/tx/0x0a0d6b265a70b8d379e0c6d952ebb6d17e97e2a006017c2e2ceea702c8b1698b) | [`0x8c3441…`](https://sepolia.basescan.org/tx/0x8c3441ea52a9e16c8aff52c5e38b1bdb8cb604abbda8ab93e5b5832d797a0b90) | [`0xe491f6…`](https://sepolia.basescan.org/tx/0xe491f6965537d0dbe094ce5ffa6897d02516094b16f233fac8cd9aa913d8f54a) | [`0x6ab9ca…`](https://lasna.reactscan.net/tx/0x6ab9ca861d92e08336d0060519de936163bbd2c0f0e98caa7329a8ab48d4a0f1) | [`0x6ab9ca…`](https://lasna.reactscan.net/tx/0x6ab9ca861d92e08336d0060519de936163bbd2c0f0e98caa7329a8ab48d4a0f1) |
| 83 | no_trade | [`0x0ff163…`](https://lasna.reactscan.net/tx/0x0ff1633a5f6b7b76748b8ac0597e1f31f6a5466f56b586889699ad44b92e068a) | [`0xdc8530…`](https://sepolia.basescan.org/tx/0xdc853065db7bc07e979cc4661ac636188835f0082dc5ba923ecc266c3749b1af) | [`0xf255e1…`](https://sepolia.basescan.org/tx/0xf255e16f0fa811cf7b9f18c5432fd3d1d9ece51dfd24061cd14e56c67f45c33b) | [`0xc364c4…`](https://lasna.reactscan.net/tx/0xc364c4c608cdde62c3bfd7a17dd83e22f05586aae8bfade61dd17c7bf5a0ec20) | [`0xc364c4…`](https://lasna.reactscan.net/tx/0xc364c4c608cdde62c3bfd7a17dd83e22f05586aae8bfade61dd17c7bf5a0ec20) |
| 84 | no_trade | [`0x6e2218…`](https://lasna.reactscan.net/tx/0x6e2218dc0498ed140a7338925db398dece765835218f0706c43e0251771f3592) | [`0x9c9012…`](https://sepolia.basescan.org/tx/0x9c9012f645bfb63551e8d8474d69dbade24c767e9f7098df5fd64f1ff2b55269) | [`0x461a7a…`](https://sepolia.basescan.org/tx/0x461a7aa35c3d3ce16cab04a88d5a37b546f3334082ecb7829b66b8259805129e) | [`0x9086f6…`](https://lasna.reactscan.net/tx/0x9086f6cbe11ec9b496f8f259e7cbf4eb54c509bfac7e513d3cd69415a811b5c4) | [`0x9086f6…`](https://lasna.reactscan.net/tx/0x9086f6cbe11ec9b496f8f259e7cbf4eb54c509bfac7e513d3cd69415a811b5c4) |
| 85 | no_trade | [`0xacf7dd…`](https://lasna.reactscan.net/tx/0xacf7dda6717d14434f034ccb243c2ea25fedc0d3154ed88728aa4b12a80975ce) | [`0xfd53bb…`](https://sepolia.basescan.org/tx/0xfd53bb252d414a4e22f101fd5ce9a3647af7550ccca22d21399d3bb1ec98ea75) | [`0x12d670…`](https://sepolia.basescan.org/tx/0x12d670b1f2fa4df7b671006d580a872872aeceef11890b69c1bdfcc7724110fe) | [`0xa6ec9b…`](https://lasna.reactscan.net/tx/0xa6ec9bcf8454f16e974202d8bb3788fe7663e06c724308d597144d5e353f3c26) | [`0xa6ec9b…`](https://lasna.reactscan.net/tx/0xa6ec9bcf8454f16e974202d8bb3788fe7663e06c724308d597144d5e353f3c26) |
| 86 | no_trade | [`0x0372f6…`](https://lasna.reactscan.net/tx/0x0372f6a93285338fbe2796796671aecff6140e85d02e3a70aef552245a609f51) | [`0xe7f445…`](https://sepolia.basescan.org/tx/0xe7f445b0961b2d95ed4a1859815409b1f54f6f10774499e84e530ad5f3bf9b99) | [`0x9b1cda…`](https://sepolia.basescan.org/tx/0x9b1cdaeb0f6eb7ddb1e1f1f6607c8ee0f0858ab197bca77a7d29f0f87f933e8a) | [`0x70be8d…`](https://lasna.reactscan.net/tx/0x70be8dfc001e6d6bb10c626586ff688a8662452043f163f3000b1a4634d37200) | [`0x70be8d…`](https://lasna.reactscan.net/tx/0x70be8dfc001e6d6bb10c626586ff688a8662452043f163f3000b1a4634d37200) |
| 87 | no_trade | [`0xdff458…`](https://lasna.reactscan.net/tx/0xdff458d91a9faa4d1f466de151c80a5c46df672072d8d585597a228c7ba848d9) | [`0x68ce82…`](https://sepolia.basescan.org/tx/0x68ce82ede35cf80b3e58354090736f35c063d6b69a619ad6ae16fd9fd012c87f) | [`0x2ad14c…`](https://sepolia.basescan.org/tx/0x2ad14c622a43a3e40c73cec5606f29b10f1f7183fc91c33395f427a3bca389ce) | [`0xa0ebb8…`](https://lasna.reactscan.net/tx/0xa0ebb8fb6ccba9b14340588b4aa554bc4a2bde1fdf9f0015ae00e2f3c67d2125) | [`0xa0ebb8…`](https://lasna.reactscan.net/tx/0xa0ebb8fb6ccba9b14340588b4aa554bc4a2bde1fdf9f0015ae00e2f3c67d2125) |
| 88 | no_trade | [`0x747d0c…`](https://lasna.reactscan.net/tx/0x747d0caa7ff20bffea4054986bab4790397ebde96eaa467ed6296b3139f72cb2) | [`0x964018…`](https://sepolia.basescan.org/tx/0x96401850242386a94195066dd52c018d0e9d7c2cf170d680dba8b69c9c98924b) | [`0x41a479…`](https://sepolia.basescan.org/tx/0x41a479621322a456ea0b1494d8ef0222315b2f018a197f23da70a5b3d1ad0e57) | [`0xa152be…`](https://lasna.reactscan.net/tx/0xa152be79ece9c86ac580600a980366ccc469149acf86a62edd4a6086f1c23058) | [`0xa152be…`](https://lasna.reactscan.net/tx/0xa152be79ece9c86ac580600a980366ccc469149acf86a62edd4a6086f1c23058) |
| 89 | no_trade | [`0x00b567…`](https://lasna.reactscan.net/tx/0x00b567517ec2aab061f6bbd8c35208c908c9d198796f885d3d986dee9c4d3640) | [`0xc79fb2…`](https://sepolia.basescan.org/tx/0xc79fb29e006cb1dcda8f124e8b6b52aa2581f7dcfe77b418897739bb76e11c82) | [`0xda8ccb…`](https://sepolia.basescan.org/tx/0xda8ccbcaa69d322e0fae4cd02664b1ebf0dc68e4d7f5911e15a380043a51d2c1) | [`0x8d10e9…`](https://lasna.reactscan.net/tx/0x8d10e910eef6b8dd833ad80252de8d82504fb7f73019722dba6e01ca1e4447c1) | [`0x8d10e9…`](https://lasna.reactscan.net/tx/0x8d10e910eef6b8dd833ad80252de8d82504fb7f73019722dba6e01ca1e4447c1) |
| 90 | no_trade | [`0x0ff415…`](https://lasna.reactscan.net/tx/0x0ff415a0247c556a2ac15dfbd718ba4d73fbd8327ae71b655d907fa70e7c251c) | [`0xcc9dfa…`](https://sepolia.basescan.org/tx/0xcc9dfa4a6a3cf827e9619052ccaca3112f7166f73577dcd781cf25c15ea3dcb9) | [`0xce5f02…`](https://sepolia.basescan.org/tx/0xce5f02431b60860e1526435009acb17055a0ac25a99004ff71eba6f3012b3e9a) | [`0xc90fab…`](https://lasna.reactscan.net/tx/0xc90fabdbde155430223692e887c95760f4f96c6704e0d096c50ca012f6e5281c) | [`0xc90fab…`](https://lasna.reactscan.net/tx/0xc90fabdbde155430223692e887c95760f4f96c6704e0d096c50ca012f6e5281c) |
| 91 | no_trade | [`0x27737c…`](https://lasna.reactscan.net/tx/0x27737cbfee1df81a974b35869914f92cec7fa3a1390a67f54af8cd93702f83dd) | [`0x7459f5…`](https://sepolia.basescan.org/tx/0x7459f58cc2ae36ff9cd2587486e86265e6af0cd392f5939e675eebf6b26d53f1) | [`0x69a419…`](https://sepolia.basescan.org/tx/0x69a419344126c55148b0acf2ed34653986d1b5d6eb2ebb4d81abb4ed07fc9a6a) | [`0x81bced…`](https://lasna.reactscan.net/tx/0x81bcedb69db0173926de3c593d8b1f7e6e0f55e822542ee75b5277782fa41b61) | [`0x81bced…`](https://lasna.reactscan.net/tx/0x81bcedb69db0173926de3c593d8b1f7e6e0f55e822542ee75b5277782fa41b61) |
| 92 | no_trade | [`0x97d6fb…`](https://lasna.reactscan.net/tx/0x97d6fb1410af75568d54dd443e45110bef398f248edf71225b8c388e6b4e525f) | [`0x0ffdbe…`](https://sepolia.basescan.org/tx/0x0ffdbe3b7d9c2a07ef77a5634dd1bcbd094176622dfcdafb3d318e60cb6759df) | [`0x2f1707…`](https://sepolia.basescan.org/tx/0x2f17072d3789556bd6734cbf194aa8c94cd7ef4351eeacff24e2a3539222aa50) | [`0x9e2e0c…`](https://lasna.reactscan.net/tx/0x9e2e0cf7f830596e8e5375ee4b5cb44adcdf42be65ad01effadefa18358ef27f) | [`0x9e2e0c…`](https://lasna.reactscan.net/tx/0x9e2e0cf7f830596e8e5375ee4b5cb44adcdf42be65ad01effadefa18358ef27f) |
| 93 | no_trade | [`0x09ac72…`](https://lasna.reactscan.net/tx/0x09ac726bd7959163961fb8a10943753a660a6c2d4a0a08713c27948725d769ab) | [`0xda46cc…`](https://sepolia.basescan.org/tx/0xda46cc31de56e728c41bcabaef01c551187d302c8e78c6a0182ff6edf4e68337) | [`0x191a1c…`](https://sepolia.basescan.org/tx/0x191a1cc52270f593233bef2c0b531ef1c29a8c067d3828fa65c8bf6622f1808c) | [`0x7562ad…`](https://lasna.reactscan.net/tx/0x7562ad562879d5cb01651b941475d978e00bf327acda647ba71dd632d5f9f61c) | [`0x7562ad…`](https://lasna.reactscan.net/tx/0x7562ad562879d5cb01651b941475d978e00bf327acda647ba71dd632d5f9f61c) |
| 94 | no_trade | [`0x23f2f8…`](https://lasna.reactscan.net/tx/0x23f2f8b2671eb0b0f4d55fe0577abc6ddb819216a153a38785e61fabb971d379) | [`0x261181…`](https://sepolia.basescan.org/tx/0x26118139dea09a6fd728b797082e92398a3140c092c5da9f9c6373ac97c23513) | [`0xc9e85a…`](https://sepolia.basescan.org/tx/0xc9e85a8c680e995e57b26b94f461312e14d50e4d0926f27a59673749559e0478) | [`0x5a8cd9…`](https://lasna.reactscan.net/tx/0x5a8cd9c90015a2011d858a0df0742f3773f09388e61ca13353dcf74c15542998) | [`0x5a8cd9…`](https://lasna.reactscan.net/tx/0x5a8cd9c90015a2011d858a0df0742f3773f09388e61ca13353dcf74c15542998) |
| 95 | no_trade | [`0xf3ca2b…`](https://lasna.reactscan.net/tx/0xf3ca2b1b682afad6b842cd4b16d9e15ecfc9493d88fb778702556f9153d3c72b) | [`0x852ff8…`](https://sepolia.basescan.org/tx/0x852ff8cd4f05dd1ae6adda224f1dfd165c9c1bba2f18d619ffd7419227eaf354) | [`0xd0da4d…`](https://sepolia.basescan.org/tx/0xd0da4db7266589af94797da918865ee781327624635061c5504a5e7f577ab80f) | [`0x42690a…`](https://lasna.reactscan.net/tx/0x42690adfb2c05cc5fac5a628ab6860d80c0e20165072d0c011e8376972060ef4) | [`0x42690a…`](https://lasna.reactscan.net/tx/0x42690adfb2c05cc5fac5a628ab6860d80c0e20165072d0c011e8376972060ef4) |
| 96 | no_trade | [`0xda8a0a…`](https://lasna.reactscan.net/tx/0xda8a0ab7a35fe20f882fe5f4238e92a8fa70ee2de162df14e4045ede6ce981c7) | [`0xc8c344…`](https://sepolia.basescan.org/tx/0xc8c344dea432e9ecf80da5e0a32a3382d3ea7081db92541a0f648f7a6cd774c9) | [`0xec25e4…`](https://sepolia.basescan.org/tx/0xec25e4a710cbdc0fe32507faf9385ba46a5eec5ced00c64bc1ba69223b8ffa97) | [`0xe7314c…`](https://lasna.reactscan.net/tx/0xe7314ce5ef0b0512a6621e9293364dd3c1526d88bf111ec3486bcd14cee25fd6) | [`0xe7314c…`](https://lasna.reactscan.net/tx/0xe7314ce5ef0b0512a6621e9293364dd3c1526d88bf111ec3486bcd14cee25fd6) |
| 97 | no_trade | [`0xb94bbb…`](https://lasna.reactscan.net/tx/0xb94bbbcd60793127626ded7a451ac39ccb7a0a3a11dbf1586ceb04a7bb764193) | [`0xcee36f…`](https://sepolia.basescan.org/tx/0xcee36f5050d38de6b5ae333a2251c516ceb5dd6187a8b1d75a0ce72165ab2423) | [`0x08dc5b…`](https://sepolia.basescan.org/tx/0x08dc5b6781ecaffd34bc8b93f11ed2dbc9f5f49908bcaccdd4cd6c07656d2f58) | [`0x7a5940…`](https://lasna.reactscan.net/tx/0x7a5940f603307728c646a3e34223be9e3cf736c8f4888a60cb2e48622b8916f7) | [`0x7a5940…`](https://lasna.reactscan.net/tx/0x7a5940f603307728c646a3e34223be9e3cf736c8f4888a60cb2e48622b8916f7) |
| 98 | no_trade | [`0x123a20…`](https://lasna.reactscan.net/tx/0x123a20b5aae09a4ba65a626c58db904715cb54a1ac15368fbc65e381f27faa91) | [`0xd22f66…`](https://sepolia.basescan.org/tx/0xd22f660841a4c1cf1dda6f5ed7da9734f7d5b4609091f8dbd111d865d9027d02) | [`0xbf994b…`](https://sepolia.basescan.org/tx/0xbf994bdce97d1b550ebfa5001bc74d9f8a47d5b384963b44ae4c00cd964fb329) | [`0xb27759…`](https://lasna.reactscan.net/tx/0xb277598d1cbbd0a36cbb9f4c068a7f30ed12fc53957371d8a0408e2204e7699d) | [`0xb27759…`](https://lasna.reactscan.net/tx/0xb277598d1cbbd0a36cbb9f4c068a7f30ed12fc53957371d8a0408e2204e7699d) |
| 99 | no_trade | [`0xffc42f…`](https://lasna.reactscan.net/tx/0xffc42fcf7a5dfdb762ce5fc75b0cdc075c8762b011002493011046595546c07d) | [`0x8aa00e…`](https://sepolia.basescan.org/tx/0x8aa00eef03bd0be5315c863c51b4dcf11c9c51852c09a90ba9b286d9ce80a498) | [`0xd41d43…`](https://sepolia.basescan.org/tx/0xd41d43b06d721bef62de01e5051f2300eed08326f14edbf187c904617ca72645) | [`0x98305f…`](https://lasna.reactscan.net/tx/0x98305f9fcc7d73d573392263ca0bace8774713f3ea7c480b15ef62764563377d) | [`0x98305f…`](https://lasna.reactscan.net/tx/0x98305f9fcc7d73d573392263ca0bace8774713f3ea7c480b15ef62764563377d) |
| 100 | no_trade | [`0x9dab28…`](https://lasna.reactscan.net/tx/0x9dab28b112bfaa0a58e9de78f474c14bc671e2ccb433000ed6a7813f5d1ce3a9) | [`0x0ecb5f…`](https://sepolia.basescan.org/tx/0x0ecb5f346e0ed119262e5f7605e24ba7aac581e5a34dd308e6eea7c8edd414fa) | [`0x12d8db…`](https://sepolia.basescan.org/tx/0x12d8db10454d9f43690d5106338cca96bfc8fe32f6db4a6407ad033cffc6fb6a) | [`0x2db4d0…`](https://lasna.reactscan.net/tx/0x2db4d0c5ea522ead1ce39899e65681d0d46192a5d0bab5013e78e13c06cb4e22) | [`0x2db4d0…`](https://lasna.reactscan.net/tx/0x2db4d0c5ea522ead1ce39899e65681d0d46192a5d0bab5013e78e13c06cb4e22) |
| 101 | no_trade | [`0x50b3ed…`](https://lasna.reactscan.net/tx/0x50b3ede747afb52e6ef352d9c2eea73d9144f3087aaa003a4fe6e4dad9b0e347) | [`0xae37fc…`](https://sepolia.basescan.org/tx/0xae37fce254256dd392f5b5fb17a98ac1ab0274203e88e3f1fbd8f051f7b7311c) | [`0xfb5539…`](https://sepolia.basescan.org/tx/0xfb5539681ad00134368c07c6c14980475258e73f27c5eafe2386d3a26ba563d8) | [`0x46f43d…`](https://lasna.reactscan.net/tx/0x46f43d62ff188d207b55fe4f86014150c4c3fbd6c19a50fe6e4cfe150fc903d6) | [`0x46f43d…`](https://lasna.reactscan.net/tx/0x46f43d62ff188d207b55fe4f86014150c4c3fbd6c19a50fe6e4cfe150fc903d6) |
| 102 | no_trade | [`0x43afbe…`](https://lasna.reactscan.net/tx/0x43afbe8618a1cc3a2c4de26c6f594646cf05cffc9d495901a4c662a3c61312cb) | [`0x0c60e2…`](https://sepolia.basescan.org/tx/0x0c60e2ccc39fcaf46d105af2ccab62566163c7b98ed3ce51f1b55a8b68bf5992) | [`0x4cdee9…`](https://sepolia.basescan.org/tx/0x4cdee9a0bb1d73ee64a0b2b704758e8f81b2f0aea3aa10cadcb47a9c4156fb98) | [`0xcc3188…`](https://lasna.reactscan.net/tx/0xcc3188d7f844df38779b19fdfefa344cc4253ab6b3c1bf5663b76bc22a7be891) | [`0xcc3188…`](https://lasna.reactscan.net/tx/0xcc3188d7f844df38779b19fdfefa344cc4253ab6b3c1bf5663b76bc22a7be891) |
| 103 | no_trade | [`0xfb65df…`](https://lasna.reactscan.net/tx/0xfb65df7e48840fa30092501b3cdde9b07a3d0a01a2fbeab9f0cf2bec3cba795b) | [`0x8cbc6d…`](https://sepolia.basescan.org/tx/0x8cbc6d0dc45de15f339fe961027cbf5282303c40aa69dde59b4aeccf95a35e17) | [`0x944700…`](https://sepolia.basescan.org/tx/0x944700573ba21388c216d1cfbc303a13b1eb7cbd910f695975d73e9b8feeba15) | [`0x773848…`](https://lasna.reactscan.net/tx/0x7738486bf7ce0c193ec46c9ba9b11ddad203b273d8fa4eb73a3d0a85cc1b1796) | [`0x773848…`](https://lasna.reactscan.net/tx/0x7738486bf7ce0c193ec46c9ba9b11ddad203b273d8fa4eb73a3d0a85cc1b1796) |
| 104 | no_trade | [`0x11906e…`](https://lasna.reactscan.net/tx/0x11906e671c338789d0be968addbe9d6b94c5642ebd8968e554df5a15748fce86) | [`0x3ddd0f…`](https://sepolia.basescan.org/tx/0x3ddd0f80c11ae37f21d7ce47f6f1381b6b5a61c8aca96f6b7f29fb21d1c80474) | [`0x5b6a65…`](https://sepolia.basescan.org/tx/0x5b6a65a76bd900be09c52abd3e334156a7172f5d2f7fd816161a4253dbde6b2e) | [`0xb6899b…`](https://lasna.reactscan.net/tx/0xb6899b022d607ccfc5a9e54ae500154175a39c6de79f7d8a159c310e43342606) | [`0xb6899b…`](https://lasna.reactscan.net/tx/0xb6899b022d607ccfc5a9e54ae500154175a39c6de79f7d8a159c310e43342606) |
| 105 | no_trade | [`0x37044d…`](https://lasna.reactscan.net/tx/0x37044dd5d01fe334a04e400fac6c864312f76481bea1b4a14b18b2a63d32ca21) | [`0x955f2c…`](https://sepolia.basescan.org/tx/0x955f2c42fd57483099a47c419583de17a53dd0ed7fe3e2f514be756ee5f307bd) | [`0x486a47…`](https://sepolia.basescan.org/tx/0x486a470d9e03351a09aca634414d95207eeec012149874d3bc7cdf39122d6746) | [`0xad39f2…`](https://lasna.reactscan.net/tx/0xad39f20b2ed8e367dcda31e20a0e88eee575e59aab16ba49941bd0bcc6b2beea) | [`0xad39f2…`](https://lasna.reactscan.net/tx/0xad39f20b2ed8e367dcda31e20a0e88eee575e59aab16ba49941bd0bcc6b2beea) |
| 106 | no_trade | [`0x436c99…`](https://lasna.reactscan.net/tx/0x436c9908ee66150e9831f588364a8754784f149dcb71e0f620b59eeecfe9b4c9) | [`0x0aee5b…`](https://sepolia.basescan.org/tx/0x0aee5bcea6868d3b354cb930c8378b488ba90f4e6ed3bbbdb69da3ce060f3888) | [`0xe5858e…`](https://sepolia.basescan.org/tx/0xe5858e5b2c07883d9fe96899570a9a703bd8aace7c4b863c820ad59c02da0f01) | [`0xe64ca3…`](https://lasna.reactscan.net/tx/0xe64ca36f8fe47eb1989755f8dbd228cdb2b53cfda9a9af9aac42ad1ead4a6c83) | [`0xe64ca3…`](https://lasna.reactscan.net/tx/0xe64ca36f8fe47eb1989755f8dbd228cdb2b53cfda9a9af9aac42ad1ead4a6c83) |
| 107 | no_trade | [`0xf7ba8b…`](https://lasna.reactscan.net/tx/0xf7ba8b132583e03258b4085f971f8f14e02ae607c3cfa0d849579b071d54b84b) | [`0xab9728…`](https://sepolia.basescan.org/tx/0xab972801fee95c1fd35a2384862e548648b6c0d4fad354b8b4711fd14815ef02) | [`0x11d6b0…`](https://sepolia.basescan.org/tx/0x11d6b0cf4201a373f31237e131977635d58572002e6a541c1191d3a98416ac2e) | [`0x5c2478…`](https://lasna.reactscan.net/tx/0x5c247842e522e6b21bbfe4a73248fb137693f543cb29256551f65e87c310633c) | [`0x5c2478…`](https://lasna.reactscan.net/tx/0x5c247842e522e6b21bbfe4a73248fb137693f543cb29256551f65e87c310633c) |
| 108 | no_trade | [`0xb1c624…`](https://lasna.reactscan.net/tx/0xb1c62462b580ec7b101bcc354c1539ea28703c12ce3da4f46c84dba460f4b84b) | [`0x097809…`](https://sepolia.basescan.org/tx/0x0978092e740e2775c02383e7c6424d0d2e26a681fc9cb284da50139a1e72f022) | [`0xe2a8a5…`](https://sepolia.basescan.org/tx/0xe2a8a5d7559e607e1bf184c91eab77390a81f234a10fcf262f0cef28e893c70c) | [`0xb3f95d…`](https://lasna.reactscan.net/tx/0xb3f95d0b2f341af65bb3d5c61f3aa594755276c7475d00cdde8eddc8cb0596cf) | [`0xb3f95d…`](https://lasna.reactscan.net/tx/0xb3f95d0b2f341af65bb3d5c61f3aa594755276c7475d00cdde8eddc8cb0596cf) |
| 109 | no_trade | [`0x0bf5f1…`](https://lasna.reactscan.net/tx/0x0bf5f1e42c15f046a4534c0928a6499c99d928983bb64362b7d19ac8e878dabe) | [`0xd8771d…`](https://sepolia.basescan.org/tx/0xd8771dcee5365f84fbd4eeb5be1536a08f10053638755b427f3cdf57f5a2eaec) | [`0x4dfaa3…`](https://sepolia.basescan.org/tx/0x4dfaa3867d2b1435ae52e83ab22109699a2d20ff68a07a52afb06332d444d740) | [`0xedb917…`](https://lasna.reactscan.net/tx/0xedb917555ae21fb603906132255c8ac6b49a455e7acdafe4fe7852a221dd107d) | [`0xedb917…`](https://lasna.reactscan.net/tx/0xedb917555ae21fb603906132255c8ac6b49a455e7acdafe4fe7852a221dd107d) |
| 110 | no_trade | [`0x840301…`](https://lasna.reactscan.net/tx/0x840301ce23c19232e9bf1015200951c2600ec7008a0f8af8194d82fef1b52d3e) | [`0x25ed4e…`](https://sepolia.basescan.org/tx/0x25ed4e1293e50a460892ddc85022013a0a0540add32a311a84c95eebb2d8f558) | [`0x082dc5…`](https://sepolia.basescan.org/tx/0x082dc5c3b039b1fbbe042f4b5033739062a66501a3c61e67c006b4fd110079a9) | [`0x72b7ee…`](https://lasna.reactscan.net/tx/0x72b7eea833452359d110c407c66979108fb60ad1a92100231b8abfed5c13f518) | [`0x72b7ee…`](https://lasna.reactscan.net/tx/0x72b7eea833452359d110c407c66979108fb60ad1a92100231b8abfed5c13f518) |
| 111 | no_trade | [`0xbf5735…`](https://lasna.reactscan.net/tx/0xbf5735655d7c522a6ec0e1a9ba88e64aac8604b665f0717bc0eab747c5727993) | [`0x0a6ce7…`](https://sepolia.basescan.org/tx/0x0a6ce7b71e165af0f6e86c6db62bba9275bc0ca919a097f7df124e8769fb764f) | [`0xcc5619…`](https://sepolia.basescan.org/tx/0xcc5619abd3eea3da2fa2140192f5fba70756a71c280f275564c5ca4268b029ad) | [`0x7458ff…`](https://lasna.reactscan.net/tx/0x7458ffad45e4874db90a13839067c978663006875c9ed46c3ea4d2e05002beab) | [`0x7458ff…`](https://lasna.reactscan.net/tx/0x7458ffad45e4874db90a13839067c978663006875c9ed46c3ea4d2e05002beab) |
| 112 | no_trade | [`0x435dd1…`](https://lasna.reactscan.net/tx/0x435dd1adadc3f7211475093441168647eb1580cdf1e126ca08bf8e89c8d167f1) | [`0xe0f990…`](https://sepolia.basescan.org/tx/0xe0f9903e6f450771b7d695911632cb40872e11a54a48e9559bdc14de48dd7749) | [`0x330bcd…`](https://sepolia.basescan.org/tx/0x330bcd8df2a8c00bf4d20d5a5f99eb03d581de02891939f0fc45f06804f5837f) | [`0x745e7e…`](https://lasna.reactscan.net/tx/0x745e7e0a0b573117c6118fe528edeebcb87945217f53002a751bf786af61b4c7) | [`0x745e7e…`](https://lasna.reactscan.net/tx/0x745e7e0a0b573117c6118fe528edeebcb87945217f53002a751bf786af61b4c7) |
| 113 | no_trade | [`0x92c3bd…`](https://lasna.reactscan.net/tx/0x92c3bd0e5585d13b008c9de878f30a4300c0b82318955b50a8e71c627018cf71) | [`0x90f4b1…`](https://sepolia.basescan.org/tx/0x90f4b101b42ee411a6b8b5df5f79da42e384665f85e8d79899d49f70e27a108e) | [`0xb10634…`](https://sepolia.basescan.org/tx/0xb1063475999beeac9b659e2e5b65554ad4e1350b4b2b2c18ed9518cf590cd66a) | [`0x65e716…`](https://lasna.reactscan.net/tx/0x65e71639b49f5797bdc1d802d427d8ca3ec537c47b01dca283fd5ce34088b69c) | [`0x65e716…`](https://lasna.reactscan.net/tx/0x65e71639b49f5797bdc1d802d427d8ca3ec537c47b01dca283fd5ce34088b69c) |
| 114 | no_trade | [`0x98c376…`](https://lasna.reactscan.net/tx/0x98c376c5e4621c7d28f4a9719243d6e6e8701074c7b17599d0d2323b22a6dc31) | [`0x00e230…`](https://sepolia.basescan.org/tx/0x00e230c48fecfb412f9469234b831df50b92e0a8cba293d629f1a4d3d909be54) | [`0xee465b…`](https://sepolia.basescan.org/tx/0xee465b3bf4b92cc602eabb1313410df0c04d87153cb2587a1040d84916584cbb) | [`0x8cc150…`](https://lasna.reactscan.net/tx/0x8cc1503353f08fe81c38a440ddceab3cc1b8c1ce3c7a4caa730a9cb860f291e9) | [`0x8cc150…`](https://lasna.reactscan.net/tx/0x8cc1503353f08fe81c38a440ddceab3cc1b8c1ce3c7a4caa730a9cb860f291e9) |
| 115 | no_trade | [`0xd7ae95…`](https://lasna.reactscan.net/tx/0xd7ae959cca10a5a97dfc7a86d458ce7f7e4ca1b5b9acb968ea854eee6749ed7f) | [`0x6beb2b…`](https://sepolia.basescan.org/tx/0x6beb2b3c74868c26ea8be8e2b77f655f55cdc110146820bc9ce4a335cf848e52) | [`0x29feed…`](https://sepolia.basescan.org/tx/0x29feed5f120adc024a8d7bb6ba5136b91c80121ab1223c4d3fc824876ff2a571) | [`0x3c687c…`](https://lasna.reactscan.net/tx/0x3c687c8f53bd7cb5a1222c690c2473367528548b192e5c87b4acf306c7fc8f4e) | [`0x3c687c…`](https://lasna.reactscan.net/tx/0x3c687c8f53bd7cb5a1222c690c2473367528548b192e5c87b4acf306c7fc8f4e) |
| 116 | no_trade | [`0x36b994…`](https://lasna.reactscan.net/tx/0x36b994408c63ba899219aaa162df0e16934661b11a46f7cfc9b63c127b21b1d1) | [`0xbd4d8e…`](https://sepolia.basescan.org/tx/0xbd4d8eed1e68e27e4b48773c4cc880dde19cc28aad8039e9078639c6567b7c04) | [`0xfbeac0…`](https://sepolia.basescan.org/tx/0xfbeac05d99e9b3367758c3bd26a7ef16d14e48e2a9161a8cb3b4583f2c441131) | [`0xe6c110…`](https://lasna.reactscan.net/tx/0xe6c11032d38055a286f7b640b41985d6754454bc477f73c1d2c5160a2fb56d94) | [`0xe6c110…`](https://lasna.reactscan.net/tx/0xe6c11032d38055a286f7b640b41985d6754454bc477f73c1d2c5160a2fb56d94) |
| 117 | no_trade | [`0x7375fc…`](https://lasna.reactscan.net/tx/0x7375fcef2c5c6b1f006539786279e353b592c6352d2b64745d9b556d17147b48) | [`0x2e60d7…`](https://sepolia.basescan.org/tx/0x2e60d7f2117fdfe22fc9eb7ee33ac80cdf9553827517d27ecb500405dd8cb721) | [`0x2cd40b…`](https://sepolia.basescan.org/tx/0x2cd40bc8ca6953f61f8082e1b1e0c82619b731d1cfaf61c2a97cc6e7e19b04d3) | [`0xbe9712…`](https://lasna.reactscan.net/tx/0xbe9712d878a303159e3ea81424c2554a9e0abb0670b666e8582fa99a9c3d5e0d) | [`0xbe9712…`](https://lasna.reactscan.net/tx/0xbe9712d878a303159e3ea81424c2554a9e0abb0670b666e8582fa99a9c3d5e0d) |
| 118 | no_trade | [`0x1fa50c…`](https://lasna.reactscan.net/tx/0x1fa50c4ee27c68644e998e44358ef7a5f8856be13c39cb8dd33d394854794d9d) | [`0x546773…`](https://sepolia.basescan.org/tx/0x546773c4ad39c79e972044657ff5918d0f8b65d195ec0856696f4b60808461f4) | [`0x6784f9…`](https://sepolia.basescan.org/tx/0x6784f9e40c185e99c35e1a539af013564b164aea3f6b5b5fa2f02ee19711b109) | [`0x46bb13…`](https://lasna.reactscan.net/tx/0x46bb13b0e048ee666bac112a7f41f72fca005caa8235e2bd0acad7eccac3f0c4) | [`0x46bb13…`](https://lasna.reactscan.net/tx/0x46bb13b0e048ee666bac112a7f41f72fca005caa8235e2bd0acad7eccac3f0c4) |
| 119 | no_trade | [`0x9c9e31…`](https://lasna.reactscan.net/tx/0x9c9e317c952ccc7c575e1fb7a4f346bd2c9a1cc7af3569235ecc029d3fcc9d52) | [`0x17d74a…`](https://sepolia.basescan.org/tx/0x17d74a33d8d83fa662c9ab20db58feaab35c7dc2b9925ef297f4aa3e0e69a791) | [`0xfa2877…`](https://sepolia.basescan.org/tx/0xfa28774def50476d4988ba4f33769659884402449c2d8f9bbe927356b744445d) | [`0x342942…`](https://lasna.reactscan.net/tx/0x342942b99d21bef3a62fd51631208e6447d9c6bb01f8fd1f6f8966d6138f0305) | [`0x342942…`](https://lasna.reactscan.net/tx/0x342942b99d21bef3a62fd51631208e6447d9c6bb01f8fd1f6f8966d6138f0305) |
| 120 | no_trade | [`0x92aaf5…`](https://lasna.reactscan.net/tx/0x92aaf50cd9f6d9ea00b292f91a10927b3da25f8f6b6f2bac5516b35dd16fd400) | [`0x6137e8…`](https://sepolia.basescan.org/tx/0x6137e88a71d8f1bbd7ad56e7a18478e3af5791523c98cc96c920daaba690c9fb) | [`0xc4c02d…`](https://sepolia.basescan.org/tx/0xc4c02d1ba8dc08a89e8c4794808217d23eb293808d1d18c443193152b7ed78ff) | [`0xbeba63…`](https://lasna.reactscan.net/tx/0xbeba631437f08b6f40b5eb1484674dbaf821f4c91a8a92d906048aefffa54a81) | [`0xbeba63…`](https://lasna.reactscan.net/tx/0xbeba631437f08b6f40b5eb1484674dbaf821f4c91a8a92d906048aefffa54a81) |
| 121 | no_trade | [`0x58020e…`](https://lasna.reactscan.net/tx/0x58020eeadd4d2ed5409d8370a103b7f9af8746387d6209e0c333f41dd4739502) | [`0xfa3b72…`](https://sepolia.basescan.org/tx/0xfa3b72f8b509c481f37c7f293719f88b9a7097f117dfa37e5577d8ec29e468ab) | [`0x3ade34…`](https://sepolia.basescan.org/tx/0x3ade34114b2854ed666639384452d4658324fc8d994511f732ea76de1d9096f6) | [`0xebf899…`](https://lasna.reactscan.net/tx/0xebf899b553397411384dcef7f1306e1720de15e485301a546c2da137c327f2c1) | [`0xebf899…`](https://lasna.reactscan.net/tx/0xebf899b553397411384dcef7f1306e1720de15e485301a546c2da137c327f2c1) |
| 122 | no_trade | [`0x2875a4…`](https://lasna.reactscan.net/tx/0x2875a4baa84018f03ff9ef5977088ac8071002e6788ba79d2df2563f88a1eddd) | [`0x29a942…`](https://sepolia.basescan.org/tx/0x29a94264af9f27155b37e44b1a8c54c568905034d7299465298a4f774204c5d0) | [`0x457c4f…`](https://sepolia.basescan.org/tx/0x457c4f422c38a825901c3a1ab716bc812658389a4b53a754221cd9b16cadbd6f) | [`0xda7291…`](https://lasna.reactscan.net/tx/0xda72916d525b4fa39602548fdcb8f38401e4e1463299204a1cb663fad233cad8) | [`0xda7291…`](https://lasna.reactscan.net/tx/0xda72916d525b4fa39602548fdcb8f38401e4e1463299204a1cb663fad233cad8) |
| 123 | no_trade | [`0x650956…`](https://lasna.reactscan.net/tx/0x650956d57b2c05d3fcaf3f449b99a5fb7cafee34cfdbb8ee7c1bde5d1e7c5396) | [`0xaa1b78…`](https://sepolia.basescan.org/tx/0xaa1b78ea6c47956ce1682bba4ef935887a4bf9068de93d98fe9c5057512df2d6) | [`0x7409b3…`](https://sepolia.basescan.org/tx/0x7409b314f54e57e1aa3fdc3e695f24a555e10cebc3fe7c2348d47cd927f6d3aa) | [`0x7bcf73…`](https://lasna.reactscan.net/tx/0x7bcf73364a9d4ace71f87f1d678fdee2848e03136ffbbb1619b981bec58b1685) | [`0x7bcf73…`](https://lasna.reactscan.net/tx/0x7bcf73364a9d4ace71f87f1d678fdee2848e03136ffbbb1619b981bec58b1685) |
| 124 | no_trade | [`0x6fb38f…`](https://lasna.reactscan.net/tx/0x6fb38fe4e88995274935203be2c777ee5bdf7e16e3325272c5a02e7fa9e618b4) | [`0xb997ac…`](https://sepolia.basescan.org/tx/0xb997acacf749e2bc1ebdbf496283efe00f09f4ec634e37455223025370edc9a4) | [`0x1724ce…`](https://sepolia.basescan.org/tx/0x1724ce8277d970e29956d88b3504b1e3901218cf35ebf9d8729c0431db6cfe0c) | [`0x43cda0…`](https://lasna.reactscan.net/tx/0x43cda0a829bd54e449c085d0ec140e6359de978887127b7e73c8e8e815bbbacc) | [`0x43cda0…`](https://lasna.reactscan.net/tx/0x43cda0a829bd54e449c085d0ec140e6359de978887127b7e73c8e8e815bbbacc) |
| 125 | no_trade | [`0x3aee86…`](https://lasna.reactscan.net/tx/0x3aee86383612969410be44cd421d9a83e92ee12505822f4cbfd59428ae3dfd3c) | [`0x9a0a62…`](https://sepolia.basescan.org/tx/0x9a0a62ac83ddfa5565eee258635464e5ffc959e9a550aac00f3b7b476e87ff91) | [`0xafbc5a…`](https://sepolia.basescan.org/tx/0xafbc5a956449ada39d73b41283413746f79793b26f6b4427b50162999bfbcb68) | [`0x525352…`](https://lasna.reactscan.net/tx/0x5253526d3a0ebb5aa9947b00cae1a9a1c8baca71fa913f73a2008a372b331eaf) | [`0x525352…`](https://lasna.reactscan.net/tx/0x5253526d3a0ebb5aa9947b00cae1a9a1c8baca71fa913f73a2008a372b331eaf) |
| 126 | no_trade | [`0xcdd87d…`](https://lasna.reactscan.net/tx/0xcdd87d41de3c6de0190920bd162284bf18782ffb09c2c754a9d1a8ff7aec611d) | [`0x00e9d9…`](https://sepolia.basescan.org/tx/0x00e9d942094e77cb1e68fb2466eee4825dad72e71d682628ef6cbf190d2e0aca) | [`0x61e822…`](https://sepolia.basescan.org/tx/0x61e82273a905fa38cfd71e0f9fa3ed7bfba2f7cff4e318f7d6e79d096f780a72) | [`0x9b1b35…`](https://lasna.reactscan.net/tx/0x9b1b35e37a752128a882730a90e195c83e35bc184e890c9a2d8073f45f91f56f) | [`0x9b1b35…`](https://lasna.reactscan.net/tx/0x9b1b35e37a752128a882730a90e195c83e35bc184e890c9a2d8073f45f91f56f) |
| 127 | no_trade | [`0xc39db3…`](https://lasna.reactscan.net/tx/0xc39db3fede8009c2ff55d60023111b8ccaf83d3a05895726ea7ecbff2e88100f) | [`0xadbaa3…`](https://sepolia.basescan.org/tx/0xadbaa32f07133aa1dd586cd40c968ef0e4c06aa5693d882337d20a553340e54c) | [`0x759813…`](https://sepolia.basescan.org/tx/0x75981332bfb73bb1fb81ecbac0861e9100a074c723fd22bb5f24f39685429276) | [`0x5f5a15…`](https://lasna.reactscan.net/tx/0x5f5a150e7f5570e2d4359713b60b68f2e2313d988fbaaa1778217ed1aff963a2) | [`0x5f5a15…`](https://lasna.reactscan.net/tx/0x5f5a150e7f5570e2d4359713b60b68f2e2313d988fbaaa1778217ed1aff963a2) |
| 128 | no_trade | [`0x6682d4…`](https://lasna.reactscan.net/tx/0x6682d4a574e05e493ff5a582be9d03356f78958737aa4bc1e6ed43436c0935da) | [`0x66bc56…`](https://sepolia.basescan.org/tx/0x66bc56199ec3fc0f35a8e01e8dd009ea01607c239dd649193a5ef9c10db52803) | [`0x1e6b48…`](https://sepolia.basescan.org/tx/0x1e6b485ec56b92bf8c5625b24da6efa364b726b4feebba2503b4668f62290f1c) | [`0x42787d…`](https://lasna.reactscan.net/tx/0x42787d5eae566d3453cdab6c48fa787f647fe7d1364a0b898839e741c4f856e7) | [`0x42787d…`](https://lasna.reactscan.net/tx/0x42787d5eae566d3453cdab6c48fa787f647fe7d1364a0b898839e741c4f856e7) |
| 129 | no_trade | [`0x220fbc…`](https://lasna.reactscan.net/tx/0x220fbce245cd7dc67124248170a743593156a40ff8c9e7bbca9b9432cdb3a582) | [`0xa9bd96…`](https://sepolia.basescan.org/tx/0xa9bd961ee11090de72ae441bb44b60bb0e938431018a883d776e44fc17cbcb37) | [`0x40c79f…`](https://sepolia.basescan.org/tx/0x40c79f92bd87fbfef57f38166a84533b0d5b6a4224d642499ffbb8be3f0e348e) | [`0x60842c…`](https://lasna.reactscan.net/tx/0x60842cb6eadb9a36d043a0b0547d1ed22a0e9108dda80321d25475d41a6cceec) | [`0x60842c…`](https://lasna.reactscan.net/tx/0x60842cb6eadb9a36d043a0b0547d1ed22a0e9108dda80321d25475d41a6cceec) |
| 130 | no_trade | [`0xde8cbb…`](https://lasna.reactscan.net/tx/0xde8cbb64ff9118afcc6ce4d87e203083334f512f933eeea6505d134736809286) | [`0xffa8ba…`](https://sepolia.basescan.org/tx/0xffa8baf4310ebf0271d2e272f922cb30287fbaa8f3b1203a4affd305d77bb89e) | [`0xbb896a…`](https://sepolia.basescan.org/tx/0xbb896ad7cdbee00050e8e36361c8f05b908a4d406a4eee46cac89ef3f25c55e5) | [`0x170f5e…`](https://lasna.reactscan.net/tx/0x170f5e8ab33f257da28e36eded49ff013e4f3720817e9f08fcb0d6daabb985f3) | [`0x170f5e…`](https://lasna.reactscan.net/tx/0x170f5e8ab33f257da28e36eded49ff013e4f3720817e9f08fcb0d6daabb985f3) |
| 131 | no_trade | [`0x7d93f9…`](https://lasna.reactscan.net/tx/0x7d93f944838f28e99a4bddf8b4e07992346f37fcdc21f8449da99d56c04b3faa) | [`0x2e0c15…`](https://sepolia.basescan.org/tx/0x2e0c15b414974470304ccfc72f0efe2293aa55048c5812b7e78d0cd7cbbcba5a) | [`0x6fc24c…`](https://sepolia.basescan.org/tx/0x6fc24c81589ae7c3e910c84d8fb89b293be1bab14c273d38fac58a531118fd02) | [`0x62d084…`](https://lasna.reactscan.net/tx/0x62d0846f5aff05e0081f4a74e9cfe82c74e99ae496cece4d8b98a050c30e8ade) | [`0x62d084…`](https://lasna.reactscan.net/tx/0x62d0846f5aff05e0081f4a74e9cfe82c74e99ae496cece4d8b98a050c30e8ade) |
| 132 | no_trade | [`0x571b83…`](https://lasna.reactscan.net/tx/0x571b83932ffaf69f3587edd59a23e239d00383bf7791e1ef3e8a1a5d6d88932e) | [`0x951b76…`](https://sepolia.basescan.org/tx/0x951b76d0053a35d7eb28cb485740da2271654feac90ddc0e91c27d5f5cf88389) | [`0xe21af5…`](https://sepolia.basescan.org/tx/0xe21af5a8f27a0b6b3716fb2e7788658d6ebe18cde64f4197306b371360927ba2) | [`0x66fdb8…`](https://lasna.reactscan.net/tx/0x66fdb82b9185c0831f42a66611425f7493e5d932f3a8c7824d49b814698becbe) | [`0x66fdb8…`](https://lasna.reactscan.net/tx/0x66fdb82b9185c0831f42a66611425f7493e5d932f3a8c7824d49b814698becbe) |
| 133 | no_trade | [`0x056dec…`](https://lasna.reactscan.net/tx/0x056dec326b55add1def1bf5995b9afa230d14ea36442971f8ab1cbe6b2edba70) | [`0x30dbd3…`](https://sepolia.basescan.org/tx/0x30dbd3e7f224ebe77a4479d5465f4f7284e41acadc03780e1e77d327106c0abe) | [`0x22c5c7…`](https://sepolia.basescan.org/tx/0x22c5c7205ee000ecd6604201d723cad11ae31bec17d4eb2eb9e29304c4328b9d) | [`0x871c38…`](https://lasna.reactscan.net/tx/0x871c3877822a89461208c4a748b3cd78514867363837a59b06dfe66868e44ca8) | [`0x871c38…`](https://lasna.reactscan.net/tx/0x871c3877822a89461208c4a748b3cd78514867363837a59b06dfe66868e44ca8) |
| 134 | no_trade | [`0xc2d521…`](https://lasna.reactscan.net/tx/0xc2d52179130e34d0d398ad81b7e48a217158a17fa1b22eeae3f9b2cfcc35d8d8) | [`0x71c7ad…`](https://sepolia.basescan.org/tx/0x71c7ad2c448e951d0af702524526c4031c1625d72ece787991a20fc87bcf5b27) | [`0x8254a7…`](https://sepolia.basescan.org/tx/0x8254a73d42e95637c295e11b5969d4daa13070924fa70a70fe79a481713d97d4) | [`0x60b14d…`](https://lasna.reactscan.net/tx/0x60b14d76036620d7857fde185f61949b1d0445f546e69537b6040567d338696a) | [`0x60b14d…`](https://lasna.reactscan.net/tx/0x60b14d76036620d7857fde185f61949b1d0445f546e69537b6040567d338696a) |
| 135 | no_trade | [`0x4923b7…`](https://lasna.reactscan.net/tx/0x4923b7ddaa7fc299bf29ceb36597e2978817075ea2646126b1e7105a3ce990fa) | [`0x25aa52…`](https://sepolia.basescan.org/tx/0x25aa52b90f59925b6517c85b90ccd3b043375567cac14a693be7caa54ba355ce) | [`0x26ecbc…`](https://sepolia.basescan.org/tx/0x26ecbcc043ab94b879c478b78df3ad96ab49f46a2fa13e51bc388df84880d9fe) | [`0x29d190…`](https://lasna.reactscan.net/tx/0x29d19049182128af67b15bcd0e70531340926c8b644c9b8e2b6d928aad45e423) | [`0x29d190…`](https://lasna.reactscan.net/tx/0x29d19049182128af67b15bcd0e70531340926c8b644c9b8e2b6d928aad45e423) |
| 136 | no_trade | [`0x1d8ffc…`](https://lasna.reactscan.net/tx/0x1d8ffcabed98d4d54e7cb55da56ed83087ab2ba7ed2ab972f75a347cc2c13a15) | [`0xde0d43…`](https://sepolia.basescan.org/tx/0xde0d43dddae853e339cb1aa400cb01a92d8adb7f918b500155229bed4643529c) | [`0x86bfe4…`](https://sepolia.basescan.org/tx/0x86bfe4c3cc4ff5b2d1800ead93caed6daa674821b46a38563d86005a9284336d) | [`0x2af64c…`](https://lasna.reactscan.net/tx/0x2af64cb6ef7eb5c850cebb6bc55145137cce136df947763d8879b642e58fdb70) | [`0x2af64c…`](https://lasna.reactscan.net/tx/0x2af64cb6ef7eb5c850cebb6bc55145137cce136df947763d8879b642e58fdb70) |
| 137 | no_trade | [`0x1d2cca…`](https://lasna.reactscan.net/tx/0x1d2ccae9494220092cfb26df40be95294f2d2949fea6caffe32e4ef9eea6018a) | [`0x8594a6…`](https://sepolia.basescan.org/tx/0x8594a654acebc1bb484ded710bc79faf5dc62dbbeffc2fa4be6747ced073d6de) | [`0x751e27…`](https://sepolia.basescan.org/tx/0x751e27a137bf3b8b3c50b741db3563db235b86dda9554241d682dbbc6de761ff) | [`0x083b6f…`](https://lasna.reactscan.net/tx/0x083b6f74fde95718917ce81ba5d803164a91a78a0201d5b1f77bd6ffe886cd03) | [`0x083b6f…`](https://lasna.reactscan.net/tx/0x083b6f74fde95718917ce81ba5d803164a91a78a0201d5b1f77bd6ffe886cd03) |
| 138 | no_trade | [`0x1c0ea4…`](https://lasna.reactscan.net/tx/0x1c0ea4e21468d50a18fed5c2d0fa24b198381c17c1a08faa00a1202b3f8b56e8) | [`0x020ecf…`](https://sepolia.basescan.org/tx/0x020ecfbbf1e26ec60cd95376abade794e682a0990de08b4dc32b073538c414e5) | [`0x0c5d37…`](https://sepolia.basescan.org/tx/0x0c5d379a2ff69553e157d198824ff7f474d482c97659e909b734af4b00514f57) | [`0x882e1c…`](https://lasna.reactscan.net/tx/0x882e1cfc6a17c1d59acc9e3093182885d9839f9a995a4c2e526ded73cedf7e98) | [`0x882e1c…`](https://lasna.reactscan.net/tx/0x882e1cfc6a17c1d59acc9e3093182885d9839f9a995a4c2e526ded73cedf7e98) |
| 139 | no_trade | [`0x761261…`](https://lasna.reactscan.net/tx/0x761261599ab062020ef498422301d8ade33533671b12b159efc354898ad1cc3c) | [`0x2f0fec…`](https://sepolia.basescan.org/tx/0x2f0fec8d71a3cf9f65ff9ea3d5d073b2b87167519d5ed9f8e998311d85887203) | [`0xa2bd46…`](https://sepolia.basescan.org/tx/0xa2bd46e7b56b3e9bb14840f29961ebd93db98652cb4de806652cab1dba538d01) | [`0x0a2de3…`](https://lasna.reactscan.net/tx/0x0a2de3a6dbcb2194fb20a90e40bf2172e8bbd88b5a545211f32c932466ce27c1) | [`0x0a2de3…`](https://lasna.reactscan.net/tx/0x0a2de3a6dbcb2194fb20a90e40bf2172e8bbd88b5a545211f32c932466ce27c1) |
| 140 | no_trade | [`0xbe7132…`](https://lasna.reactscan.net/tx/0xbe7132ea17b878ac1ea5a637754761e14269944203f488215eea8abec984449a) | [`0x9dc010…`](https://sepolia.basescan.org/tx/0x9dc010c9b0f087f52d53c19c9264926f3874b9d23d10882dbd00c4ff6bde1c87) | [`0x3c313c…`](https://sepolia.basescan.org/tx/0x3c313cc78aedee895a028afdaa2d42d3c12ba18879365dab0ace0751c67dfa2a) | [`0xae08c9…`](https://lasna.reactscan.net/tx/0xae08c98177c140df4353fad0d90c7a31634183b4553de324ee907648a7c9b9cd) | [`0xae08c9…`](https://lasna.reactscan.net/tx/0xae08c98177c140df4353fad0d90c7a31634183b4553de324ee907648a7c9b9cd) |
| 141 | no_trade | [`0xc04c33…`](https://lasna.reactscan.net/tx/0xc04c33bb33ff9cc3058018d1d90827170c85c789c9b2521180de197b6a40abb7) | [`0xa7a97a…`](https://sepolia.basescan.org/tx/0xa7a97ab514f9f75cd99fa56a50cd880b051c687ade81fae4508c8dac99427292) | [`0xd9a858…`](https://sepolia.basescan.org/tx/0xd9a8581a92faac44cbc584bc4d0bc6599e9d99f9ec1d24c00ba11bea30e8acd2) | [`0x586961…`](https://lasna.reactscan.net/tx/0x586961e9e3220134a2f016d7a37bb2f380a9660804710f78ad11a273eebaaf87) | [`0x586961…`](https://lasna.reactscan.net/tx/0x586961e9e3220134a2f016d7a37bb2f380a9660804710f78ad11a273eebaaf87) |
| 142 | no_trade | [`0xca7bc1…`](https://lasna.reactscan.net/tx/0xca7bc12c74d2475d2130a7a1f9997cefaced7bb3994830068f635ec660bbffe1) | [`0x6bb053…`](https://sepolia.basescan.org/tx/0x6bb053c4b721ba56de8972d975d8bedbc2cf339789b8ae47cbfbae7d84c95bd1) | [`0x04c782…`](https://sepolia.basescan.org/tx/0x04c782905e3c50a9cb677b2aacaf55fa547d9e746ebdce1304bf4c68ce5851c9) | [`0x86bacf…`](https://lasna.reactscan.net/tx/0x86bacf1f2da4fb5201b1cb358c50755bd0c2be829cfbc97f514603dd41938cd0) | [`0x86bacf…`](https://lasna.reactscan.net/tx/0x86bacf1f2da4fb5201b1cb358c50755bd0c2be829cfbc97f514603dd41938cd0) |
| 143 | no_trade | [`0xd1b630…`](https://lasna.reactscan.net/tx/0xd1b6300fdd08a55f35e51ddf3e9109f5063c50493b52f0172b4c65733a41abd8) | [`0x5beb71…`](https://sepolia.basescan.org/tx/0x5beb713df107e256966119e431922ae6d56ee2078836e0c74e98e85f5ce5c2ec) | [`0x0b5c34…`](https://sepolia.basescan.org/tx/0x0b5c34cf08436e926f3ac0901de34ae1e76f212cdde619c28f1b0a9c4738a6f4) | [`0x42e091…`](https://lasna.reactscan.net/tx/0x42e0910578f1fd7cc94a3415ce7857641caaffabe970661ad3bcc5f64311fb5f) | [`0x42e091…`](https://lasna.reactscan.net/tx/0x42e0910578f1fd7cc94a3415ce7857641caaffabe970661ad3bcc5f64311fb5f) |
| 144 | no_trade | [`0xc9e0d3…`](https://lasna.reactscan.net/tx/0xc9e0d32e0a769eb8abc0a9c5d3bf219cfa304ff76930b279a77a6326630266f3) | [`0x2eb88f…`](https://sepolia.basescan.org/tx/0x2eb88f1acd1f4167d07828f8bdd83152c52e0d738d1a8913b8bd4b39394db732) | [`0x5756b7…`](https://sepolia.basescan.org/tx/0x5756b7c214f8f59d8ec30bfc32298e908a0c9eb5805343bbf982791931d82f97) | [`0x572f44…`](https://lasna.reactscan.net/tx/0x572f444b9f19db5a3f4923511e8aebd1e0991c68cdef4cd3415cd2496e2de4dd) | [`0x572f44…`](https://lasna.reactscan.net/tx/0x572f444b9f19db5a3f4923511e8aebd1e0991c68cdef4cd3415cd2496e2de4dd) |
| 145 | no_trade | [`0x7222bb…`](https://lasna.reactscan.net/tx/0x7222bbc2878888eab0de64c8b30c3b8e71bedfbd7e723149247496233204fbbf) | [`0x109a74…`](https://sepolia.basescan.org/tx/0x109a748bff30799e4ae30afed1d6cc0caf188eccea8b4b6390024d30f8f165d6) | [`0xdda687…`](https://sepolia.basescan.org/tx/0xdda687be7b57b9d1f25926d1e1385017cbcd538ecbb38e21c4f28d9edb01ef9c) | [`0x6b99ed…`](https://lasna.reactscan.net/tx/0x6b99ed4989bcbb1dcdaef8b1f432a45384fd9321c4d727cf1ce47712a6c27f0f) | [`0x6b99ed…`](https://lasna.reactscan.net/tx/0x6b99ed4989bcbb1dcdaef8b1f432a45384fd9321c4d727cf1ce47712a6c27f0f) |
| 146 | no_trade | [`0x7aae1a…`](https://lasna.reactscan.net/tx/0x7aae1ac50ca4bc881dc07cf13ef47404e9f4175f0a130e588c84b747d0e7a2c5) | [`0x732d3e…`](https://sepolia.basescan.org/tx/0x732d3eff5ddec65043d87011ad2e160a3cf5f7c79043289a2f53d88e4d60aeb7) | [`0x612e62…`](https://sepolia.basescan.org/tx/0x612e625d15cdd4f0bd699c8daf786733f0f28d348e7129e26ec75b146f89399f) | [`0xcd3f68…`](https://lasna.reactscan.net/tx/0xcd3f680cd4afe912776951cb48e9d8ee9527d06b995f63915637031dd8b0e515) | [`0xcd3f68…`](https://lasna.reactscan.net/tx/0xcd3f680cd4afe912776951cb48e9d8ee9527d06b995f63915637031dd8b0e515) |
| 147 | no_trade | [`0xeab5da…`](https://lasna.reactscan.net/tx/0xeab5daa48ee3c4ce11492b5379594fe6907cdf0fd8f87675e3112cedeeb0c0a8) | [`0xbd0971…`](https://sepolia.basescan.org/tx/0xbd0971e23beddf31dc81e516e3341e7cdbabad9c9bfd3771ee7c0a508f6b1a4a) | [`0x31d91c…`](https://sepolia.basescan.org/tx/0x31d91cd20b24c0da6efcbec5954f8ba6e7805c9b9f9d88efdafa4216bd3ac521) | [`0x87088b…`](https://lasna.reactscan.net/tx/0x87088bc72133fdd1476c4714cc81502bcf460ca3d86c72f0f8a116951f97fe93) | [`0x87088b…`](https://lasna.reactscan.net/tx/0x87088bc72133fdd1476c4714cc81502bcf460ca3d86c72f0f8a116951f97fe93) |
| 148 | no_trade | [`0xa60b40…`](https://lasna.reactscan.net/tx/0xa60b40493db633e55159b64911241f6c098caccde0e40065c4e0d649cb297500) | [`0xf81da8…`](https://sepolia.basescan.org/tx/0xf81da81abe3e894ae64540b8aebc6c373d469603abd4fdfa82a57acd92065c41) | [`0x24a275…`](https://sepolia.basescan.org/tx/0x24a27565c7d6a5c29f953ca652a322e7f401bcc4711e172791d55293ea1c0052) | [`0x012898…`](https://lasna.reactscan.net/tx/0x012898bcd33bc714006c46b9ef29d15360bfbbc1087275b4f8f23550875a4189) | [`0x012898…`](https://lasna.reactscan.net/tx/0x012898bcd33bc714006c46b9ef29d15360bfbbc1087275b4f8f23550875a4189) |
| 149 | no_trade | [`0x3c18e2…`](https://lasna.reactscan.net/tx/0x3c18e22462a6d25801c9bd4944ae4ee8e8171900c8d904913034dc44224cc909) | [`0xc85436…`](https://sepolia.basescan.org/tx/0xc854361444efaa8ec18c49166179e4f51b01e9214ad515777e5e54a93ee343bb) | [`0x1dfd0c…`](https://sepolia.basescan.org/tx/0x1dfd0c195e4b4bcc943be282425e4b354097b7c0d0c28d6d995a1c93e3af8125) | [`0x0f0aed…`](https://lasna.reactscan.net/tx/0x0f0aed968fe1dda76e53915925f58a1ddb9d5e8dff131cd440065a8e80147acf) | [`0x0f0aed…`](https://lasna.reactscan.net/tx/0x0f0aed968fe1dda76e53915925f58a1ddb9d5e8dff131cd440065a8e80147acf) |
| 150 | no_trade | [`0x4b7e26…`](https://lasna.reactscan.net/tx/0x4b7e269b8ed28a4e3140a2183ff804bd763cf379052cb896d26a68fa76dc64e5) | [`0x37fbba…`](https://sepolia.basescan.org/tx/0x37fbba6ba30760b607de1dbb366ae16cd6a77a62a2d509ff1a9ffe39dd8e3729) | [`0x1226ca…`](https://sepolia.basescan.org/tx/0x1226ca589fbfb84a62fcd98b02137ed8afc9c57bd07ca95f2523a054298d215d) | [`0xa1fc3e…`](https://lasna.reactscan.net/tx/0xa1fc3e7b81a8a476dda91780b4a2c798e3aa0f23567a28ea4977b28fac53a2c0) | [`0xa1fc3e…`](https://lasna.reactscan.net/tx/0xa1fc3e7b81a8a476dda91780b4a2c798e3aa0f23567a28ea4977b28fac53a2c0) |
| 151 | no_trade | [`0xcc0914…`](https://lasna.reactscan.net/tx/0xcc091430433b080cda9bb594ee85532dd96670902225416651b9f2d76cedacc4) | [`0x6e9972…`](https://sepolia.basescan.org/tx/0x6e9972b47ad2260333d865a6ca7f84c0537b8e5d48abb2fc1b50182e001e1a2f) | [`0xfae914…`](https://sepolia.basescan.org/tx/0xfae91437956ca3c9b4c1f0facb599e85414deb2c33e2344e690fb6b343a5bb99) | [`0xae15d5…`](https://lasna.reactscan.net/tx/0xae15d527f551974e91b5939017fe4be2651af0f103e96cb7cbf39f205ff3bfeb) | [`0xae15d5…`](https://lasna.reactscan.net/tx/0xae15d527f551974e91b5939017fe4be2651af0f103e96cb7cbf39f205ff3bfeb) |
| 152 | no_trade | [`0x0e4abc…`](https://lasna.reactscan.net/tx/0x0e4abc3be066c3785907e843a159363d94b48787cb9cbe7ea0de95437c60351d) | [`0x2205cc…`](https://sepolia.basescan.org/tx/0x2205cce430b7017204483d39a8532a893f9e52e3827cc78e815566b85a41fd55) | [`0x68556a…`](https://sepolia.basescan.org/tx/0x68556a39408325f22ca95435185e42b27abec25fd4b90089cc43d678bf7ec8b8) | [`0x7a8278…`](https://lasna.reactscan.net/tx/0x7a8278ea6ce204ae29f4fc31e7b6ecb438b94b1b990e98d80217242fd66a9864) | [`0x7a8278…`](https://lasna.reactscan.net/tx/0x7a8278ea6ce204ae29f4fc31e7b6ecb438b94b1b990e98d80217242fd66a9864) |
| 153 | no_trade | [`0xe60231…`](https://lasna.reactscan.net/tx/0xe602315c2e94606de59f4640ba28a0478a0347d29a9565bc8bc699029bce5099) | [`0x53badc…`](https://sepolia.basescan.org/tx/0x53badc065bc986c0d142d25c6bdfe8f6cdedb252661d6b14d97838aacd8884d0) | [`0x87a021…`](https://sepolia.basescan.org/tx/0x87a021770e6452eda252d7366f0cae500a2caf630b555b3768d375f5fcac38fb) | [`0x63e320…`](https://lasna.reactscan.net/tx/0x63e32030da5e8b8d0088476bc57d24598206095c87f01a08791f1c9e6a085e2b) | [`0x63e320…`](https://lasna.reactscan.net/tx/0x63e32030da5e8b8d0088476bc57d24598206095c87f01a08791f1c9e6a085e2b) |
| 154 | no_trade | [`0x8e212d…`](https://lasna.reactscan.net/tx/0x8e212dbe823cf6d3e91441cff959143d7260979c1b15efa2b7a30abe840eead4) | [`0x175615…`](https://sepolia.basescan.org/tx/0x1756157eb863ab70f159fba33390ddb4bc127b40a84c42dd3a34eb84d5accfe4) | [`0x112e01…`](https://sepolia.basescan.org/tx/0x112e013d2afd6dd9227db90e66bc65449f67bf3bfb5f45ce1282f0dc15823d07) | [`0x81de87…`](https://lasna.reactscan.net/tx/0x81de87fe80451eb54209ba864da68d2bf4de01ef0be7323fa845251b9294b5f5) | [`0x81de87…`](https://lasna.reactscan.net/tx/0x81de87fe80451eb54209ba864da68d2bf4de01ef0be7323fa845251b9294b5f5) |
| 155 | no_trade | [`0xe1e454…`](https://lasna.reactscan.net/tx/0xe1e454473ac50e9f5cb89a6806f6d74eb49a347287f2234f0090ee43d56689fd) | [`0xf8c6df…`](https://sepolia.basescan.org/tx/0xf8c6dfb7e3924a2308bfb911385fc750323ecf9bfe1555b87d3d8dd15d32dfc0) | [`0x54f1c2…`](https://sepolia.basescan.org/tx/0x54f1c23c970aa32ded100e6815a4e4115594d29ad5e6585e58c5bdc37d3c50ae) | [`0xf95db6…`](https://lasna.reactscan.net/tx/0xf95db6c7dce4f21905ccce1a65aa8d04ab35ffce1912434af56d3575daa16628) | [`0xf95db6…`](https://lasna.reactscan.net/tx/0xf95db6c7dce4f21905ccce1a65aa8d04ab35ffce1912434af56d3575daa16628) |
| 156 | no_trade | [`0x0c9851…`](https://lasna.reactscan.net/tx/0x0c98510a5dd7bc6e7cf223ac330675ee19effebc06b528e8cf9e897f5e5ce66e) | [`0x1d1bc0…`](https://sepolia.basescan.org/tx/0x1d1bc0bdcf1a4f2a2b92c6a8cb49570049365b5162a5173d3758c52711aed9e0) | [`0x2e6932…`](https://sepolia.basescan.org/tx/0x2e693281cb459d6b3a651d28036debfd2dde0762a0423bb25add33121342b9c2) | [`0x0b27e3…`](https://lasna.reactscan.net/tx/0x0b27e3e5d7b5130d7a40552399ecc60a2c98ba7fc6cfab80828dce467cd26446) | [`0x0b27e3…`](https://lasna.reactscan.net/tx/0x0b27e3e5d7b5130d7a40552399ecc60a2c98ba7fc6cfab80828dce467cd26446) |
| 157 | no_trade | [`0x6a8d71…`](https://lasna.reactscan.net/tx/0x6a8d7167c74ee2ab3c220f4d8407de9e2f03ac1a707c817f5ce881979d14e9c3) | [`0x3001ee…`](https://sepolia.basescan.org/tx/0x3001ee63b390f3b9802fa734a5884926b415c20ba741ebea044c6ea889237199) | [`0x27c571…`](https://sepolia.basescan.org/tx/0x27c571b2afbbbf070448ae76192043b49c05220cbc3978305a306866f78c4894) | [`0xa1aa44…`](https://lasna.reactscan.net/tx/0xa1aa44a1e7f30621b567369d2cece0977cb348bb64cc9c013c1d817899b2f197) | [`0xa1aa44…`](https://lasna.reactscan.net/tx/0xa1aa44a1e7f30621b567369d2cece0977cb348bb64cc9c013c1d817899b2f197) |
| 158 | no_trade | [`0x87d950…`](https://lasna.reactscan.net/tx/0x87d950bb25e55c8e98b429aa540c362cb672df223bdc7e8452d444080daca5c4) | [`0x6d3fb1…`](https://sepolia.basescan.org/tx/0x6d3fb133679fff0fdb0342c4f18618e62d35faf5a9f9f838a11e9cb32abd5d22) | [`0x6f000b…`](https://sepolia.basescan.org/tx/0x6f000b51049a025269a43af1fc597d699d75f0388f9cf46c92b25cf890c56ac6) | [`0xa5d6b2…`](https://lasna.reactscan.net/tx/0xa5d6b2e4fb1bc1148201a999bf410d4c987f511058ba1197cda1e79ae5bdf07f) | [`0xa5d6b2…`](https://lasna.reactscan.net/tx/0xa5d6b2e4fb1bc1148201a999bf410d4c987f511058ba1197cda1e79ae5bdf07f) |

## The five things the judges are asked to look for

1. **A clamped proposal.** Cycle 1: the model asked for 7102 bps, the contract allowed 0 bps. Clamp bits: LP_ABOVE_MAX, ECONOMIC_VETO. Transaction: [`0xdfa515…`](https://lasna.reactscan.net/tx/0xdfa5152aaac0e6c654ca358c6eba1866757ea3ce5e8361e12b7bce3d7018b651)
2. **The economic veto.** Cycle 1: the contract measured a fee edge under its own threshold and sent the allocation to zero on its own. Clamp bits: LP_ABOVE_MAX, ECONOMIC_VETO. Transaction: [`0xdfa515…`](https://lasna.reactscan.net/tx/0xdfa5152aaac0e6c654ca358c6eba1866757ea3ce5e8361e12b7bce3d7018b651)
3. **Funds actually moving.** Cycle 2: the vault took a 4000 bps liquidity position worth $40,000.00 out of a $100,000.00 vault. Transaction: [`0xd3e33f…`](https://sepolia.basescan.org/tx/0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19)
4. **The contract acting without the model.** Cycle 10: the contract measured 1801 bps of volatility, over the user's exit level, and pulled the position to zero with no proposal in sight. Transaction: [`0x8f01d4…`](https://lasna.reactscan.net/tx/0x8f01d459591e2448bade1580c5be0d868ed03cf32cea8be838de133a0e728633)
5. **A proposal refused before execution.** Cycle 9: refused with CYCLE_MISMATCH. The agent's proposal carries no authority: the contract checked it and threw it away. Transaction: [`0x4b56e9…`](https://lasna.reactscan.net/tx/0x4b56e9bed865264e93255c3f7476e08739bbc519b2ac1ef390e77435ca843f7e)

## Latency across the whole loop

The event announcement asks for latency measured across the full loop, not one leg of it. The numbers below are the gap between the block the contract opened the cycle in and the block the vault's rebalance landed in, and the gap between opening the cycle and the agent's proposal.

| Cycle | Open → proposal | Open → enforced | Open → funds moved |
| --- | --- | --- | --- |
| 1 | 163s | 163s | — |
| 2 | 41s | 40s | 42s |
| 3 | 105s | 104s | — |
| 4 | 85s | 85s | — |
| 5 | 69s | 69s | — |
| 6 | 64s | 64s | — |
| 7 | 116s | 115s | — |
| 8 | 141s | 141s | — |
| 9 | 108s | — | — |
| 13 | 514s | 513s | 515s |
| 14 | 159s | 158s | — |
| 15 | 36s | 35s | — |
| 16 | 39s | 39s | — |
| 17 | 34s | 34s | — |
| 18 | 54s | 55s | — |
| 19 | 28s | 28s | — |
| 20 | 34s | 35s | — |
| 21 | 50s | 51s | — |
| 22 | 49s | 48s | — |
| 23 | 39s | 39s | — |
| 24 | 32s | 32s | — |
| 26 | 39s | 39s | — |
| 27 | 27s | 27s | — |
| 28 | 26s | 25s | — |
| 29 | 27s | 26s | — |
| 30 | 27s | 26s | — |
| 31 | 26s | 25s | — |
| 32 | 29s | 28s | — |
| 33 | 27s | 27s | — |
| 34 | 25s | 25s | — |
| 35 | 27s | 26s | — |
| 36 | 27s | 26s | — |
| 37 | 57s | 57s | 58s |
| 38 | 53s | 52s | — |
| 39 | 36s | 36s | — |
| 40 | 33s | 33s | — |
| 41 | 31s | 30s | — |
| 42 | 36s | 35s | — |
| 43 | 38s | 37s | — |
| 44 | 32s | 31s | — |
| 45 | 28s | 27s | — |
| 46 | 35s | 35s | — |
| 47 | 35s | 34s | — |
| 48 | 33s | 33s | — |
| 49 | 31s | 31s | — |
| 50 | 40s | 40s | — |
| 51 | 27s | 27s | — |
| 52 | 32s | 32s | — |
| 53 | 36s | 36s | — |
| 54 | 34s | 34s | — |
| 55 | 27s | 27s | — |
| 56 | 26s | 26s | — |
| 57 | 26s | 25s | — |
| 58 | 28s | 28s | — |
| 59 | 25s | 24s | — |
| 60 | 31s | 31s | — |
| 61 | 28s | 28s | — |
| 62 | 28s | 28s | — |
| 63 | 26s | 26s | — |
| 64 | 25s | 24s | — |
| 65 | 26s | 26s | — |
| 76 | 175s | 175s | — |
| 77 | 40s | 39s | — |
| 78 | 39s | 38s | — |
| 79 | 46s | 46s | — |
| 80 | 59s | 58s | — |
| 81 | 90s | 90s | — |
| 82 | 88s | 88s | — |
| 83 | 47s | 47s | — |
| 84 | 117s | 117s | — |
| 85 | 36s | 36s | — |
| 86 | 35s | 34s | — |
| 87 | 48s | 48s | — |
| 88 | 34s | 33s | — |
| 89 | 31s | 30s | — |
| 90 | 42s | 42s | — |
| 91 | 35s | 35s | — |
| 92 | 37s | 36s | — |
| 93 | 37s | 37s | — |
| 94 | 37s | 37s | — |
| 95 | 32s | 32s | — |
| 96 | 38s | 38s | — |
| 97 | 37s | 36s | — |
| 98 | 34s | 33s | — |
| 99 | 29s | 28s | — |
| 100 | 33s | 33s | — |
| 101 | 39s | 38s | — |
| 102 | 36s | 35s | — |
| 103 | 32s | 31s | — |
| 104 | 29s | 28s | — |
| 105 | 28s | 27s | — |
| 106 | 27s | 26s | — |
| 107 | 30s | 30s | — |
| 108 | 32s | 31s | — |
| 109 | 31s | 31s | — |
| 110 | 33s | 32s | — |
| 111 | 30s | 29s | — |
| 112 | 33s | 32s | — |
| 113 | 30s | 30s | — |
| 114 | 33s | 33s | — |
| 115 | 31s | 30s | — |
| 116 | 35s | 34s | — |
| 117 | 34s | 34s | — |
| 118 | 43s | 43s | — |
| 119 | 41s | 40s | — |
| 120 | 40s | 40s | — |
| 121 | 36s | 36s | — |
| 122 | 38s | 38s | — |
| 123 | 58s | 57s | — |
| 124 | 30s | 30s | — |
| 125 | 33s | 33s | — |
| 126 | 99s | 99s | — |
| 127 | 77s | 76s | — |
| 128 | 115s | 114s | — |
| 129 | 73s | 72s | — |
| 130 | 101s | 100s | — |
| 131 | 40s | 39s | — |
| 132 | 32s | 32s | — |
| 133 | 41s | 40s | — |
| 134 | 36s | 36s | — |
| 135 | 53s | 52s | — |
| 136 | 85s | 85s | — |
| 137 | 44s | 44s | — |
| 138 | 66s | 65s | — |
| 139 | 30s | 30s | — |
| 140 | 49s | 49s | — |
| 141 | 66s | 66s | — |
| 142 | 56s | 55s | — |
| 143 | 63s | 63s | — |
| 144 | 33s | 33s | — |
| 145 | 31s | 30s | — |
| 146 | 36s | 36s | — |
| 147 | 32s | 31s | — |
| 148 | 32s | 32s | — |
| 149 | 32s | 32s | — |
| 150 | 30s | 30s | — |
| 151 | 57s | 56s | — |
| 152 | 40s | 40s | — |
| 153 | 39s | 38s | — |
| 154 | 60s | 60s | — |
| 155 | 34s | 33s | — |
| 156 | 39s | 38s | — |
| 157 | 34s | 33s | — |
| 158 | 577s | 577s | — |

* Open → proposal: median **36s**, worst **577s** over 144 cycles.
* Open → enforced: median **35s**, worst **577s** over 143 cycles.

## Full transaction hashes

| Cycle | Leg | Chain | Transaction hash |
| --- | --- | --- | --- |
| 1 | opened | Lasna | `0x8389609044c23d05dfd4c9ee3e94a1dd2d8cf128d0ba192508bbc40b67cde089` |
| 1 | requested | Base Sepolia | `0xedb5507a8dc60a559397e4617f6804b37b0ee4e9cc58166c1a1d12f7423efc3c` |
| 1 | posted | Base Sepolia | `0x9000153cff80d1d8d52263bfaffd42660c4657244d9f5ca779c0ee4d604a5b29` |
| 1 | evaluated | Lasna | `0xdfa5152aaac0e6c654ca358c6eba1866757ea3ce5e8361e12b7bce3d7018b651` |
| 1 | noTrade | Lasna | `0xdfa5152aaac0e6c654ca358c6eba1866757ea3ce5e8361e12b7bce3d7018b651` |
| 2 | opened | Lasna | `0x01a2ab43f717831ff4a2b9d5092210d83e4cdfed9b4e206f0245c0be7a948c34` |
| 2 | requested | Base Sepolia | `0x01de5b2b05cc5d4ce7baf896340c08462a0ff3c27d024aac62897eadce9476d5` |
| 2 | posted | Base Sepolia | `0x465a48e0fde71a2fafff5fdada8785ec42b4ce9129ab7ab169aae67d484dd980` |
| 2 | evaluated | Lasna | `0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070` |
| 2 | rebalanceRequested | Lasna | `0xebd2fb0a4d66dd2ca62ae68af90932ca7d92a7bf3e377fc9e90e0b89c9d23070` |
| 2 | rebalanced | Base Sepolia | `0xd3e33f0e1dd7122cd3b0fcb1629305e2690ab86726d970c24910bd80667f0a19` |
| 3 | opened | Lasna | `0xdd906e0099a1c04fa1eedd2e1509c4732fa910464ef4bf0dff0b8051ac7eed67` |
| 3 | requested | Base Sepolia | `0xc6c22c51b755c1041b499290d984f4561206c454418fd9593680d60ade911f41` |
| 3 | posted | Base Sepolia | `0x78ac45223b61d2df05bf66822b4cb3876541a0313987c4fab3896325b0d56b38` |
| 3 | evaluated | Lasna | `0xe5095bf7ba8fc77afe15208c72b4a22734b002bf6ccf3ab66a96398595887121` |
| 3 | noTrade | Lasna | `0xe5095bf7ba8fc77afe15208c72b4a22734b002bf6ccf3ab66a96398595887121` |
| 4 | opened | Lasna | `0x0f3011b01b04086e807f08aae69913cb3f6fb80a6450806ac97d2037e232d65d` |
| 4 | requested | Base Sepolia | `0x48e96b95651b205c33e5a35671a4d7e36d26f33333a19a41f8becb0912c93bd4` |
| 4 | posted | Base Sepolia | `0x3fdb7a21af31a7bdb23ba6776f3cbee4e46e95dd5fde98adba30b37198825f40` |
| 4 | evaluated | Lasna | `0xad7c59d88e7c046cbe629ad350537d8da1854437d51a38c6c8f2b0ac7b4a86b9` |
| 4 | noTrade | Lasna | `0xad7c59d88e7c046cbe629ad350537d8da1854437d51a38c6c8f2b0ac7b4a86b9` |
| 5 | opened | Lasna | `0x7c585d89604141944322b385baf78b172dadd32bbcca79757603f840be72c73f` |
| 5 | requested | Base Sepolia | `0xa3382ecea191cfb43f0e784ad9fb0f51cdc2b1ac3e2d1aef583681adbb0de45f` |
| 5 | posted | Base Sepolia | `0x91586b018684c8bf6258bc724da6f1a1ffff4f85635c4a45e20b0b85ac962f3d` |
| 5 | evaluated | Lasna | `0xf8078cebbf85185091b015728feaef7ad723da03dfdb698cc3110fb34f524d59` |
| 5 | noTrade | Lasna | `0xf8078cebbf85185091b015728feaef7ad723da03dfdb698cc3110fb34f524d59` |
| 6 | opened | Lasna | `0x2858ef8165d436c0dfbee8a25aab921db82ac66b11dcf041feea109e8b030451` |
| 6 | requested | Base Sepolia | `0xda8eb3d48eb7d3fec87113ba9b84388576c947f8779ffa6e1a940e02447fe174` |
| 6 | posted | Base Sepolia | `0xfbbbbe20c88f0ef2c4b8e35ea43b5721d7c50b7cf3effc0cfd92f786a01e2740` |
| 6 | evaluated | Lasna | `0xa96ac77fdfa95cf907a31ffc6c25458b5828e423ced711790140ba05bd4c22fe` |
| 6 | noTrade | Lasna | `0xa96ac77fdfa95cf907a31ffc6c25458b5828e423ced711790140ba05bd4c22fe` |
| 7 | opened | Lasna | `0xcc48db98513d7c84fbf0b52ac4a498ff2d43b52416dd7a6750950cfa8b6dc6e2` |
| 7 | requested | Base Sepolia | `0x832474cf4398555d1fbb47a0ddc3c315b7b1a7714ccf1ecdda70d0d978e883e1` |
| 7 | posted | Base Sepolia | `0x053c7f1a75edc7e6aa53cf6f67f69bea79c760ca1542ef6c0d865300d275c988` |
| 7 | evaluated | Lasna | `0x01a5856e731e104ba490893a883fab5712896c19bb57efb20c5e90ee90ad4c0d` |
| 7 | noTrade | Lasna | `0x01a5856e731e104ba490893a883fab5712896c19bb57efb20c5e90ee90ad4c0d` |
| 8 | opened | Lasna | `0xc13c7238ce95b80aa719b506883d12ed38544f254ac98c1d58b22d0ec9e4a9b3` |
| 8 | requested | Base Sepolia | `0xf7496c0b744c3a3ccfebcb341360d6f90c611a87a32a57637bc0dd1c92a3d4de` |
| 8 | posted | Base Sepolia | `0xce42ce6403a1b1e0321baf7589461b2109a142e7491141731fe433e047f9cce8` |
| 8 | evaluated | Lasna | `0xe48045872db488e0a5e69ba62bba82c48c52d35873e4aa2dbf8fde3f44bf5c94` |
| 8 | noTrade | Lasna | `0xe48045872db488e0a5e69ba62bba82c48c52d35873e4aa2dbf8fde3f44bf5c94` |
| 9 | opened | Lasna | `0xa82eab3f0b064e53a8db7012b1564b8bd0ea5e84c7783d165d44de00489a4834` |
| 9 | requested | Base Sepolia | `0xe8d13e1d9b1856ca53cd107e56663655c50371c71aa8f040eddec1c7cdf51e39` |
| 9 | posted | Base Sepolia | `0xe283b3880634f2bf4d0e0394f07b77f6453548a7e09cd9fa9cefa57148762579` |
| 9 | rejected | Lasna | `0x4b56e9bed865264e93255c3f7476e08739bbc519b2ac1ef390e77435ca843f7e` |
| 10 | rebalanceRequested | Lasna | `0x8f01d459591e2448bade1580c5be0d868ed03cf32cea8be838de133a0e728633` |
| 10 | rebalanced | Base Sepolia | `0xf044fbf02967a0ab057b3ccebf7f4a2464b261d190f166b299fabf4617fc34d0` |
| 10 | autonomousExit | Lasna | `0x8f01d459591e2448bade1580c5be0d868ed03cf32cea8be838de133a0e728633` |
| 11 | opened | Lasna | `0x4b280093cbc5719a89275da7917513960e510511e26e7569c38b60f04744cd83` |
| 11 | requested | Base Sepolia | `0xe4f9df3e517ef059a5aa9b4fafe47386f2cf18b5e0f7d0b0e5c40bac88706692` |
| 12 | opened | Lasna | `0x05a25404fb9d88e4fbc78434d66725236a6a95bb8db38b7e5481e5799c3882cf` |
| 12 | requested | Base Sepolia | `0x3adccedc177bc719a9d7ffd5cfa0b3ea05e763a9132d6c468b8a8f662514330d` |
| 13 | opened | Lasna | `0x7179665d346fc0daf87b8f43d659f7fc8dfb06c6412f1eccff51fcf9a2a33296` |
| 13 | requested | Base Sepolia | `0x9d158c84f144fdea206b5913c014e19137118c6b578b705fa13de7a0ee3771f2` |
| 13 | posted | Base Sepolia | `0x58da1bf95d8bd7d1d37b2bc53b3629f82a5e8afd53cfab3f086dea379c3371e2` |
| 13 | evaluated | Lasna | `0x544fe3c634e9e32c5a3d6b480e03a90944f2ac82c41f43e4b48dcd68d0bebc71` |
| 13 | rebalanceRequested | Lasna | `0x544fe3c634e9e32c5a3d6b480e03a90944f2ac82c41f43e4b48dcd68d0bebc71` |
| 13 | rebalanced | Base Sepolia | `0x0439a062a321d60cf7e506eb5c1f845c3954af7012b68db4d6a60c7051016ca4` |
| 14 | opened | Lasna | `0x2b373f427a630ce00950a5a336ed683e315f213668db8cafa23fe13f3a23eb37` |
| 14 | requested | Base Sepolia | `0xbb2926598f2dae68fd22fe4a5c8330fb40cdb1ca5af78bb44fac895edf7b2620` |
| 14 | posted | Base Sepolia | `0xd060a4deffe3ec24d65638eb6d27e5b36a0d2be233b19e566928cd690c2f9d5b` |
| 14 | evaluated | Lasna | `0x237e172aad28e7dc7286d0bb05f81d3425b7b449fa5656633dc6b3fc1f593fca` |
| 14 | noTrade | Lasna | `0x237e172aad28e7dc7286d0bb05f81d3425b7b449fa5656633dc6b3fc1f593fca` |
| 15 | opened | Lasna | `0x0a60a9bf20841d4be0a4f3474ca30b05f003f4418be4eeb634cbe3a5ade97b17` |
| 15 | requested | Base Sepolia | `0x05daf3cc08a24f6fc0990bd0007ee7e51db9ae51c027fc3b5c0b98291ff38fda` |
| 15 | posted | Base Sepolia | `0x82056494d57bea079b74da750b3baa0751ebc7d7fce24eeac5de3c3d59c6de9f` |
| 15 | evaluated | Lasna | `0xdfd54c6825796c7297d057af2500fc3a593545494c8482adc762c52bd62def18` |
| 15 | noTrade | Lasna | `0xdfd54c6825796c7297d057af2500fc3a593545494c8482adc762c52bd62def18` |
| 16 | opened | Lasna | `0xf05e7ebac34d0566429b55c923aa4859d285cf5976136b84a022e9692b9077dc` |
| 16 | requested | Base Sepolia | `0xc78a48bdc4b671ade7918f45670576ad91943de3a29959b32813f520f0aab91d` |
| 16 | posted | Base Sepolia | `0x0cbf21d7d296bd2c49227748bf3c2d2145602a5546f85cafc599989c7a275d25` |
| 16 | evaluated | Lasna | `0x38997d63e281a6d18b913a45075d85ec87a4e48940163b6060ddba48b5a7f0de` |
| 16 | noTrade | Lasna | `0x38997d63e281a6d18b913a45075d85ec87a4e48940163b6060ddba48b5a7f0de` |
| 17 | opened | Lasna | `0xf307f534ac323bca9c1a8bf5b8d175d7fefe6dca198317342fc336e05f7ea7ce` |
| 17 | requested | Base Sepolia | `0x4e591772a7ff4846312f463a8dee7d450c1401fc6513249b9248e48e309684fa` |
| 17 | posted | Base Sepolia | `0xb4aef1066b9c89680a5e43f4cef1321cb44c7a7ebdc747f78e9483d933ea543d` |
| 17 | evaluated | Lasna | `0x0d32b81a7e97d1780d5d828e8a1d2388c57586b11be5d87bb86b1277cd073951` |
| 17 | noTrade | Lasna | `0x0d32b81a7e97d1780d5d828e8a1d2388c57586b11be5d87bb86b1277cd073951` |
| 18 | opened | Lasna | `0xbe72b700e47816865a935d0fbf842019b2d2de44d8ad151fd41ad5943909df56` |
| 18 | requested | Base Sepolia | `0x488257fa01baef580202525d806e5eb46ee7836601729848053b4f937e6cf398` |
| 18 | posted | Base Sepolia | `0x2918857ae85f9593e65776f808443a5e2b0dae9d409d77824de75bc7eb12fa02` |
| 18 | evaluated | Lasna | `0x98b0bee7e0342d31b33e2c6e464dc3e4968168e1070e214b26d3303544434290` |
| 18 | noTrade | Lasna | `0x98b0bee7e0342d31b33e2c6e464dc3e4968168e1070e214b26d3303544434290` |
| 19 | opened | Lasna | `0x48de69ca6bb263bab7671538427a4b68a89a5a9ff32f89488bc42087c9ff8fc4` |
| 19 | requested | Base Sepolia | `0x3971532dc9080b67ced7a16209ccefc981d1532b51d9465ecb444b9a54fc6e65` |
| 19 | posted | Base Sepolia | `0xcf2edcf151deb709140002e8ed7d37b23eb088ee4a83c8e4567650eba925d76c` |
| 19 | evaluated | Lasna | `0x58acf326434024c9f4f9029d96d5eef80b851f7427f2fe1ec306fea1f75af882` |
| 19 | noTrade | Lasna | `0x58acf326434024c9f4f9029d96d5eef80b851f7427f2fe1ec306fea1f75af882` |
| 20 | opened | Lasna | `0x5b09c51244f1b0fbd4a3995a8540d6efb8a8ffd855ca45e0f99d0aa4d8722a0b` |
| 20 | requested | Base Sepolia | `0x17b5a31a27b143f3e6cf6c260d84d3e96f1505b347312a1656b973f22d3b85f3` |
| 20 | posted | Base Sepolia | `0x351b5e1cebe0e3a12b3ef6b42623856a78e8ab9859599458ef36369ed32f306b` |
| 20 | evaluated | Lasna | `0x6fa4ac4a9ff929d6d831fa3ed384a9c53f18c20226c5bb9d1b0d4ba18f757aad` |
| 20 | noTrade | Lasna | `0x6fa4ac4a9ff929d6d831fa3ed384a9c53f18c20226c5bb9d1b0d4ba18f757aad` |
| 21 | opened | Lasna | `0x2cf4f10de921f8d585fd250798d2f64ee8ad4651bee2143b9684380d1e64d324` |
| 21 | requested | Base Sepolia | `0x518b419da1cd6f7a7d7fda1c339adaf0b3bf3bfa96bbb7e96aec5a3a320dbdfe` |
| 21 | posted | Base Sepolia | `0xf7f6db352d05400bb52aee9430fbc8955a449d7e357355171d1c521a5252fd11` |
| 21 | evaluated | Lasna | `0xc9177bd479c5d22bf9150c63e12f026a0c756cc1d638716e6fc769ee77a09492` |
| 21 | noTrade | Lasna | `0xc9177bd479c5d22bf9150c63e12f026a0c756cc1d638716e6fc769ee77a09492` |
| 22 | opened | Lasna | `0x789305c5110c7deda4f62e37e5afac171028ad484c0215515aad34b733f44e27` |
| 22 | requested | Base Sepolia | `0x7e4f2b08f96604eddf7ec3def229fc2c6269869a8fc3a346662e0f5a667612c7` |
| 22 | posted | Base Sepolia | `0xd6092f07398d5c49610caea28267f5b1ad921bfa0e54a40bedef942bc19a9bd0` |
| 22 | evaluated | Lasna | `0x75188f5de6aa432b30d8e0b18a5bfa301ca58c243d5b009c2991ebaf1ffd0be3` |
| 22 | noTrade | Lasna | `0x75188f5de6aa432b30d8e0b18a5bfa301ca58c243d5b009c2991ebaf1ffd0be3` |
| 23 | opened | Lasna | `0x32e796c2f2c1390b2cfb11ed06679d4e28a2fcc20cef5f7b9be180a3143ea230` |
| 23 | requested | Base Sepolia | `0x7b93256773ffedf681e60ce67a4f6185b68f47b37f81da439d8c4f71bda1ba3a` |
| 23 | posted | Base Sepolia | `0x9df282798bd166b96c29fc1db7d59111825bcb03b7fcdc42213a308e7f7e694d` |
| 23 | evaluated | Lasna | `0x2735b593f3b126a311d814f8ed8b12c10680aa77029c4683daa0885b0f9b19c6` |
| 23 | noTrade | Lasna | `0x2735b593f3b126a311d814f8ed8b12c10680aa77029c4683daa0885b0f9b19c6` |
| 24 | opened | Lasna | `0xe3c0febacea9893274e2ffaf12675256b952c7f26e41bd3d9fb669b66a6ea302` |
| 24 | requested | Base Sepolia | `0xcc8112832eaa936c9439e2ae4e134f0d379f8ce94557a2021336be40c9b7db5d` |
| 24 | posted | Base Sepolia | `0xc5dce1d99e3d03ad4c7d19d504da3aa2982757840753d9297139f1636141c264` |
| 24 | evaluated | Lasna | `0xac771ea54e9f17c3d4589db616c7097683d4a5f0f8803fd7a1b2fe335f58dc2f` |
| 24 | noTrade | Lasna | `0xac771ea54e9f17c3d4589db616c7097683d4a5f0f8803fd7a1b2fe335f58dc2f` |
| 25 | opened | Lasna | `0x732d85634fb2c200e1573b7de5fbe375897a6100c75bfb7c57e4f7bd1ccfda84` |
| 25 | requested | Base Sepolia | `0x5e292cc84e07bbd282f8593068df17897735cd38020199ecff3eb11a40f8d597` |
| 26 | opened | Lasna | `0x5d56bf9dae8ff90e10b390390bea564309996df7ffa007998fde048c8e98fe62` |
| 26 | requested | Base Sepolia | `0x464910eeb06eff810a62bb2dd3b72912b943cd4132f3853404a8077b627cd88b` |
| 26 | posted | Base Sepolia | `0x490c7401e1795758ec1df4604fe787381c2cd076fcc3ade204ae6e202812b6e6` |
| 26 | evaluated | Lasna | `0x012e5b4995d6ff17967e32fb56e007cea7c09ac45135bcb4dace2d5505368522` |
| 26 | noTrade | Lasna | `0x012e5b4995d6ff17967e32fb56e007cea7c09ac45135bcb4dace2d5505368522` |
| 27 | opened | Lasna | `0x03388c596780925fb31d1610cde42663af28cd944721606a650cc9a36e7fae65` |
| 27 | requested | Base Sepolia | `0xbcd6fe6f819560105837f2a25a3ea5e73cb8787a273ecc73aaab7a390c75a666` |
| 27 | posted | Base Sepolia | `0x84ccaea95c2c167e4ef5a1427184c50ae04b570a8c7a973cde14535734829e37` |
| 27 | evaluated | Lasna | `0x64d0d557cf9046e8946eab50a9fc7ea7ff1097d46a04151800696196e3bc56c8` |
| 27 | noTrade | Lasna | `0x64d0d557cf9046e8946eab50a9fc7ea7ff1097d46a04151800696196e3bc56c8` |
| 28 | opened | Lasna | `0xc76c5c7bbd43a34172db584173f8d267506ec04aea4ae7db1a6fad8257ff559d` |
| 28 | requested | Base Sepolia | `0x57174e99d1bb1492dbe4bab6a2b9b935142dd91b61421dbd5e3ecc300995925c` |
| 28 | posted | Base Sepolia | `0xc7ff5e227802d7ecb5353c1f91499edf7a89ba61451e79a772323651ce65a740` |
| 28 | evaluated | Lasna | `0xdcea313f8d571d5555760d9146391c3bae209246ddba198e86d1d2ae6db9ee86` |
| 28 | noTrade | Lasna | `0xdcea313f8d571d5555760d9146391c3bae209246ddba198e86d1d2ae6db9ee86` |
| 29 | opened | Lasna | `0xc12b8b38419c39ff9455b2a8b3beb5758b363aa21b8f4c34c6ef878dbda3e3e4` |
| 29 | requested | Base Sepolia | `0xa5ef368e26f85e8ba955f4a5ba3eca69cb4d6f6cefc7e47042fd21b3d13dcffb` |
| 29 | posted | Base Sepolia | `0xe12f6de898f9ffe69f7c900853cf792d80c8e15f6a8aef0c766043de04de3ce8` |
| 29 | evaluated | Lasna | `0x92b4d5252776e5f395a760a46090a847b254f70658711b03bd01dd0ce3670eb0` |
| 29 | noTrade | Lasna | `0x92b4d5252776e5f395a760a46090a847b254f70658711b03bd01dd0ce3670eb0` |
| 30 | opened | Lasna | `0x7a0ef62e3f8304c3c54aaf58c25dd0b733e87eeaeff7878c000f959e26e7875d` |
| 30 | requested | Base Sepolia | `0xa16b1cb62bf4b881d58f538e16d01040b0af6815a581638a4768344cef859b2a` |
| 30 | posted | Base Sepolia | `0xc046fa60db2089768d612fdd8f1cb86dcd7d343a115fa283781240981015db25` |
| 30 | evaluated | Lasna | `0x7aa5745e9b69591f6e17a4c32aada5af52a6b6451f6fe2a4d6d4675714783b18` |
| 30 | noTrade | Lasna | `0x7aa5745e9b69591f6e17a4c32aada5af52a6b6451f6fe2a4d6d4675714783b18` |
| 31 | opened | Lasna | `0x964b8f8a23d25afd291f2b257a7b8f991ad1fa7e40995a970ef1218bf0e8e5cf` |
| 31 | requested | Base Sepolia | `0x6ec7b66be2f03ab62d374fa2be283a691a409fb7f27fe8aa8789a15a320a3725` |
| 31 | posted | Base Sepolia | `0x1bb40fddbfbe7ae02c155e925dd2dd986b5ef95b36dc017c78f4f0c3edbbe205` |
| 31 | evaluated | Lasna | `0x454f2a55c2439ddfc0bafa70e4dae80ef46d60e0219d51cc5ef1cbc91dc50433` |
| 31 | noTrade | Lasna | `0x454f2a55c2439ddfc0bafa70e4dae80ef46d60e0219d51cc5ef1cbc91dc50433` |
| 32 | opened | Lasna | `0x8fdc6b76c12c56a0b071273f537c39fbdedbc30e47dd81d49116f44ea21a55a9` |
| 32 | requested | Base Sepolia | `0xda4a234e8dcf0ec3fabc21e671128d6115a2bedae291f19902611fe41d788ace` |
| 32 | posted | Base Sepolia | `0x7eae081cdc1fd85115475f74ff859bee3f2ade361876406435cfc05389a6f987` |
| 32 | evaluated | Lasna | `0xd6d2c6540d23ef1a3ff421d950c22123071a00af8a30bb3c53e655fbc611243c` |
| 32 | noTrade | Lasna | `0xd6d2c6540d23ef1a3ff421d950c22123071a00af8a30bb3c53e655fbc611243c` |
| 33 | opened | Lasna | `0x76e9bc96b400de8d053bd314ad4269bb42cc53b15cba0c7612fbf8973720a3b8` |
| 33 | requested | Base Sepolia | `0xa62be50e7887c04bf027af1883433112230dc49bd43ffaf062b289b9bce8f406` |
| 33 | posted | Base Sepolia | `0x795922bcc5d022c5ea5f5cfb0a220246c6e03577349fa68febcf7713081ffd8d` |
| 33 | evaluated | Lasna | `0x0e344da0efa75d5fc87f0bc1e51fd7b622a3f4206827c9e66018abaf4fa355f9` |
| 33 | noTrade | Lasna | `0x0e344da0efa75d5fc87f0bc1e51fd7b622a3f4206827c9e66018abaf4fa355f9` |
| 34 | opened | Lasna | `0x26180c64bad7a2ba6ddeeca34680dcdb183df23443b4e23940c5aba7cd3f5efe` |
| 34 | requested | Base Sepolia | `0x1c3ff068a6249693420d17e16bf141d9c5793c345dddab9ddc31cfe9bcc02c94` |
| 34 | posted | Base Sepolia | `0xa1d4ac8bbaa0d5bd4859c99e04a75b5fb84953b1dc27a8c4851cc215404e8195` |
| 34 | evaluated | Lasna | `0x6f424ad21fd34e83d9e83f4753052b9f0457b2f51ed8a7cda69a5e938fe27d0e` |
| 34 | noTrade | Lasna | `0x6f424ad21fd34e83d9e83f4753052b9f0457b2f51ed8a7cda69a5e938fe27d0e` |
| 35 | opened | Lasna | `0xebac9b1281ba776c77a5a80a6215b929303fea4f6fcf218116e302c4e50223c2` |
| 35 | requested | Base Sepolia | `0xb5bd472307175635d9482ab2acabb1994fbffae31e30a03ccd943c1fa86636e1` |
| 35 | posted | Base Sepolia | `0xe7bea283303b826ecc87405bacf209ee8d144daa81c2ad03078b2f8e4ab233f0` |
| 35 | evaluated | Lasna | `0x6e623b1b8266d5169681677d8dc1c0820e30dd91bfe9350fc7f354965602fc1c` |
| 35 | noTrade | Lasna | `0x6e623b1b8266d5169681677d8dc1c0820e30dd91bfe9350fc7f354965602fc1c` |
| 36 | opened | Lasna | `0x6b087644f0b6c8de038e4f9a548ca189f1d70842f8d3da89b6dabafe9809aaa7` |
| 36 | requested | Base Sepolia | `0x59e80169e7d02b7f23029b4ca7c156cdbbd83747cb51be7009a7a95ecfe2c8fe` |
| 36 | posted | Base Sepolia | `0xf651a09c92d94c85fed4a2411444bcd427d12efaa6a8702f8fb5f5e45752e9a0` |
| 36 | evaluated | Lasna | `0xbf0077bb6f5f9b4cdd9308fa693bdfe9baa21822bc905bde5afec637bed69c3f` |
| 36 | noTrade | Lasna | `0xbf0077bb6f5f9b4cdd9308fa693bdfe9baa21822bc905bde5afec637bed69c3f` |
| 37 | opened | Lasna | `0xd546d45568977025a7bd60e6695871f923e3a1a33623559354babfb2832c3908` |
| 37 | requested | Base Sepolia | `0x889d0946911861b7f53fcb29144b4a982fa1264ddf3cabae45488a9c632a33ba` |
| 37 | posted | Base Sepolia | `0x13fe3944decb8580753b90934be077e946b6de775e3a9b1218d29b7ee52d9d3f` |
| 37 | evaluated | Lasna | `0x0d2845aa3c3dd6e30863c29f836871d72e65813bc4974d741893a949912d6e58` |
| 37 | rebalanceRequested | Lasna | `0x0d2845aa3c3dd6e30863c29f836871d72e65813bc4974d741893a949912d6e58` |
| 37 | rebalanced | Base Sepolia | `0x6c23b7fda15cdb86f27d99ccc6572c48cdc8c3af4d792f4638feab909ba2a1d8` |
| 38 | opened | Lasna | `0x42aa676d6d375f6a3a6adb723ca2bd15a8d87ea4e6f227dc837c061689c3ba94` |
| 38 | requested | Base Sepolia | `0x0f6fa6c8c25083c9e1ddab6a5c6f53123cfd37eca61391ddb70b92f9ad85e576` |
| 38 | posted | Base Sepolia | `0x9c710488ebfd4618f1e45cd1db8caaab76f895700efbcfecd6e46d4f1557a3f1` |
| 38 | evaluated | Lasna | `0xec82a50ce78152d420e8008389dac8823011550569f7cd16c53a57c66701a013` |
| 38 | noTrade | Lasna | `0xec82a50ce78152d420e8008389dac8823011550569f7cd16c53a57c66701a013` |
| 39 | opened | Lasna | `0x15c8d9091ed4cb6f67b0a3af884c62261f219f596dafccb17ae2f4cd55d0009b` |
| 39 | requested | Base Sepolia | `0x2e23090803c1c1d48f0312fa1c6040d5987b06dde832f77be5d023ccface9d58` |
| 39 | posted | Base Sepolia | `0xb28e9224e243cf2a17c996f905e6d5e96cb67d4a48927c56eb3459e8e23ade60` |
| 39 | evaluated | Lasna | `0xf716dcfe11ec2e5994af522a1987246f61dc989d48b9faab3c514ebb5f54e8f1` |
| 39 | noTrade | Lasna | `0xf716dcfe11ec2e5994af522a1987246f61dc989d48b9faab3c514ebb5f54e8f1` |
| 40 | opened | Lasna | `0x40032b38bffecbcdb1fc289cb6ec245c37e43b11ac0614b44f71108b60412938` |
| 40 | requested | Base Sepolia | `0xdeef422406b9a28aa5837f718aa63b3cb37810b82f0219c01f2e004ed79c76d9` |
| 40 | posted | Base Sepolia | `0xd58c6770b0d525922bf5553746ffe266d4664db0ee85bf699a7cf400e70f3b68` |
| 40 | evaluated | Lasna | `0x0cb25b833db2479b5d44d64dc15cc7dae5a3e8b427c7cc69fe4bde46ec52baf2` |
| 40 | noTrade | Lasna | `0x0cb25b833db2479b5d44d64dc15cc7dae5a3e8b427c7cc69fe4bde46ec52baf2` |
| 41 | opened | Lasna | `0xdcaa408d14e97d0357753af93a7825af5f22b719c7ab973a8c1783055d569f0c` |
| 41 | requested | Base Sepolia | `0xa59097fcc34228f86776e58389bae6f017d63c522081cf17cf9476fec3a51ab2` |
| 41 | posted | Base Sepolia | `0xb88bc55174ff7d63074f0bd1c9f5564d2c96b9bd362834ffa77854c5c37b2bdf` |
| 41 | evaluated | Lasna | `0xbccd17ec7217be26d8199a7403fa7436bc75371377acaec0c916a8b782beb95c` |
| 41 | noTrade | Lasna | `0xbccd17ec7217be26d8199a7403fa7436bc75371377acaec0c916a8b782beb95c` |
| 42 | opened | Lasna | `0x140e836f7ee48e31ce621e1810e4c07bb05fad9d474047b8024c9b6cfd309043` |
| 42 | requested | Base Sepolia | `0xe5a67dce3c7f27d04037147938e7f0b266757d7279870338f37b76babac4c7b8` |
| 42 | posted | Base Sepolia | `0x47022d947f1b57dcc755073f923ed874d6240295ead01ff8e3e8008423055f7c` |
| 42 | evaluated | Lasna | `0x3fa495a597f912b8c37bb975b6d380d900f7be40592003d6b145119ee2b495b8` |
| 42 | noTrade | Lasna | `0x3fa495a597f912b8c37bb975b6d380d900f7be40592003d6b145119ee2b495b8` |
| 43 | opened | Lasna | `0x2622861beb89b468b7401f90fca9c5a29567989fa1a7e8628d7877a8929a8050` |
| 43 | requested | Base Sepolia | `0x2e0d78adb31bba39b2dca1db0fdda825ee4976909ef8313cee1e8500a27d77be` |
| 43 | posted | Base Sepolia | `0x1f31bd5395722730fd53f528c3dc42e4dfaa2d6e56cdf3484814668987df2425` |
| 43 | evaluated | Lasna | `0x5be31e0a330b53ecdb4072466051ace2e3bb042f02b3da5ca7712f43941792e7` |
| 43 | noTrade | Lasna | `0x5be31e0a330b53ecdb4072466051ace2e3bb042f02b3da5ca7712f43941792e7` |
| 44 | opened | Lasna | `0x1fb730bb9b5eac45ab4d97e1971739f5878844728ce818dc1d4a7d430a6c96d7` |
| 44 | requested | Base Sepolia | `0xb79d6f810e50ffee285fcb718b824d16ab7f6fd16df98a891ae4ca416de7053a` |
| 44 | posted | Base Sepolia | `0xc5e726e97344662cbc42c8bd4b55a81c8cbea5e9a82b882cc2d54645e018b8d5` |
| 44 | evaluated | Lasna | `0x9b3b34829156d00968175adac88455ed3be50bdec28455b963284879615412b1` |
| 44 | noTrade | Lasna | `0x9b3b34829156d00968175adac88455ed3be50bdec28455b963284879615412b1` |
| 45 | opened | Lasna | `0x853603c04a46e950638ca9780a59931418cefb864602c007a94c0eed0ac5ab33` |
| 45 | requested | Base Sepolia | `0xb89ff4aa66c27a4a3203d765c1699138d9f7a8f35183dda83b18edfc53a42b69` |
| 45 | posted | Base Sepolia | `0xcd678d82537f720d8edaf6906042c26f9dde0af3865b9f81eb7e7ebf34755520` |
| 45 | evaluated | Lasna | `0xcaf7afbdd893a8f98d83af9756e93eef411e76ae061dbd3ba007fd94caafa9be` |
| 45 | noTrade | Lasna | `0xcaf7afbdd893a8f98d83af9756e93eef411e76ae061dbd3ba007fd94caafa9be` |
| 46 | opened | Lasna | `0x0a8b33ff22843ec3c0cae099a2b3ba15c8da9ab0eb81c441847ba883740d1630` |
| 46 | requested | Base Sepolia | `0xb581b828bfa36e2ad48994bfdaac80cb42432fce2eef6bb0463264adcaf2e6a1` |
| 46 | posted | Base Sepolia | `0x4d0741d48188812abd3041d47668cecead22e612c7e427ca72560dbe2010583d` |
| 46 | evaluated | Lasna | `0x6fe2352b78b332c81b728604a6c7bb312c7f0cd0625daf84500568762e1448fb` |
| 46 | noTrade | Lasna | `0x6fe2352b78b332c81b728604a6c7bb312c7f0cd0625daf84500568762e1448fb` |
| 47 | opened | Lasna | `0x27d3d7d2a4e7a49c82137d74206d5675015f23c3804c38178e7a924295f64190` |
| 47 | requested | Base Sepolia | `0x9767a6d4dbdfe375e30f57f4606d49cd162881f659e408197457c71653aa6124` |
| 47 | posted | Base Sepolia | `0x3191957613b23135fc2d184caa77d27ed5241c4aaffc98a77f182a4a77f8f722` |
| 47 | evaluated | Lasna | `0x1843b72918002b2c08d7b7be239b6ebd0264563262fca06fabb47318d45e4959` |
| 47 | noTrade | Lasna | `0x1843b72918002b2c08d7b7be239b6ebd0264563262fca06fabb47318d45e4959` |
| 48 | opened | Lasna | `0x014260404a1f0623bcebbd68eda88d4f52ef91b48a85d4f425ca1dfe765a12c3` |
| 48 | requested | Base Sepolia | `0xbbb9980d4d10954a27a13cf3ec9818510b957a7863c2e1b22981c822ffb3e631` |
| 48 | posted | Base Sepolia | `0x54c3d165c058b38a59cb4e1863423fdef2250718a0bd276dfff4d4f9c84563a6` |
| 48 | evaluated | Lasna | `0x54e3ba38092a3ed58ee080d915853e2212ba8e11fff15c095f70a5c08624f21d` |
| 48 | noTrade | Lasna | `0x54e3ba38092a3ed58ee080d915853e2212ba8e11fff15c095f70a5c08624f21d` |
| 49 | opened | Lasna | `0x7dbe7c2e1bbf90c6f85366ce5affe8369d91987f3b6c5c0031ac65439c525710` |
| 49 | requested | Base Sepolia | `0xfda12e4f064b376cca8dc1a60b4a74627338f2d5b7518fce98052b00c4bab368` |
| 49 | posted | Base Sepolia | `0x4734baf5655947c4984c96557189d0add103bd0591931d0706bbe9a07cbc48d3` |
| 49 | evaluated | Lasna | `0xcdec5de88b4405f6a86f5564facdae4f41c1be8e0ee9f4d26741f936c0f322d9` |
| 49 | noTrade | Lasna | `0xcdec5de88b4405f6a86f5564facdae4f41c1be8e0ee9f4d26741f936c0f322d9` |
| 50 | opened | Lasna | `0x3adc4fa577726e2f80885f08ae8c8aaacac1ddadda8e8721cd76f11301b28be9` |
| 50 | requested | Base Sepolia | `0x40455676f0bf61dd1a74b8f1749d0ee417a962ef1c043a10da695ecf5457d51d` |
| 50 | posted | Base Sepolia | `0x4f66f5493e020b0017615aeaee928293244aa56559258e1c98e0a42f07f7eec6` |
| 50 | evaluated | Lasna | `0x864b867625fe9db65e16e084adf06c00dde5ee8a31ecdeaa71451f61a9a7a633` |
| 50 | noTrade | Lasna | `0x864b867625fe9db65e16e084adf06c00dde5ee8a31ecdeaa71451f61a9a7a633` |
| 51 | opened | Lasna | `0x01aa93183f678db7b245f48e6a1e3eea73f4cc048028891a5900ece85f04ab32` |
| 51 | requested | Base Sepolia | `0xcfad1cc47679add21b8094be17e79a36b00e50d08f8c82b03dce4c102457418b` |
| 51 | posted | Base Sepolia | `0xa3638285baf68b217e38b07ba511a1c6801f99e170c1ac82733204834de865ac` |
| 51 | evaluated | Lasna | `0x5b6957bd36e1114d9d0873c785a366dcf998e2d49081dd0cd18ad67b946807f3` |
| 51 | noTrade | Lasna | `0x5b6957bd36e1114d9d0873c785a366dcf998e2d49081dd0cd18ad67b946807f3` |
| 52 | opened | Lasna | `0x497e07061f62c1c40a23d95e16bb48f6b920e6ae2104c0599732e47c2755da2e` |
| 52 | requested | Base Sepolia | `0xd2bd5b405ff76c101196836c4cce6c395763d1f4afd6a6ddfea6398a7c57147c` |
| 52 | posted | Base Sepolia | `0x0ab2c7be9408cf4f0469c4266e32aaba129e94228444589c277ecfb195a0fa4e` |
| 52 | evaluated | Lasna | `0xbe156a86bb14cb5bd856fb52f08fe86c3001316214d4e5d0238aa819047a89d6` |
| 52 | noTrade | Lasna | `0xbe156a86bb14cb5bd856fb52f08fe86c3001316214d4e5d0238aa819047a89d6` |
| 53 | opened | Lasna | `0x89375e99f088f236c4b61cb01d12155c2e73231073627bdaba5d656b03b5ae9a` |
| 53 | requested | Base Sepolia | `0x22b0236b515f1ff1f1383ea8828a93d17ccff51be3ba1cd92dca9c24bbe6428e` |
| 53 | posted | Base Sepolia | `0x5ad739dbbdd70f35238bda1d947e82bf6dd3fbff942ff85053d6958fe77d25e8` |
| 53 | evaluated | Lasna | `0x42fb26a9a666ae4b9d7d0e4070ee767d88afecadb61f636ffd47bc252ac7cf23` |
| 53 | noTrade | Lasna | `0x42fb26a9a666ae4b9d7d0e4070ee767d88afecadb61f636ffd47bc252ac7cf23` |
| 54 | opened | Lasna | `0xf1290499eccf3f96431f97557071edbe2bea7aeadf31e5ea81617ae84d307594` |
| 54 | requested | Base Sepolia | `0x744c4aba642492229c5d86b528e261a3f78bbb31aed7e7c0ae6a063161c6a9fc` |
| 54 | posted | Base Sepolia | `0x305b9ff5a16285a93dcbee8c0ad38ef033f294a9f03b74b7fab7adc3a15bb9c1` |
| 54 | evaluated | Lasna | `0x86f31f42298cbd013d17cc035cc9da44d852e9a21a8caf39a8a512527e319c01` |
| 54 | noTrade | Lasna | `0x86f31f42298cbd013d17cc035cc9da44d852e9a21a8caf39a8a512527e319c01` |
| 55 | opened | Lasna | `0x6931d689554396ddf7c1018a32bd5844bd1c33eeb5f564b0ef7e50cb62492b0a` |
| 55 | requested | Base Sepolia | `0x74087a0a67b05440dd416449b31df13a32298c83d612cf35b4fd2da535a95647` |
| 55 | posted | Base Sepolia | `0x418cabddd1de297c6f506f271942dc5ceac851add3ad97bbbb8ed2af30b22861` |
| 55 | evaluated | Lasna | `0x5ff59f0b48f9ca499fcaf373aad9f0ac60c8455e8aff66cd98dff9679958b399` |
| 55 | noTrade | Lasna | `0x5ff59f0b48f9ca499fcaf373aad9f0ac60c8455e8aff66cd98dff9679958b399` |
| 56 | opened | Lasna | `0x824f803cbdcf26f153451a31ac5e4e191799b89879ebbfc3efc0e09114c4b714` |
| 56 | requested | Base Sepolia | `0xf54caca9fbbf1b443d37901966c9d5dd38742d233d8fa4f7eb247d3501736201` |
| 56 | posted | Base Sepolia | `0xcedc3cba6eef4cb122556d15c874c58c40a9e747c3565c1c7dfce9f8ba0d87b7` |
| 56 | evaluated | Lasna | `0xb37d2639439df06a704ef6e8adf2f2c6ccd75fec7e6bfc0973561526c0cc373a` |
| 56 | noTrade | Lasna | `0xb37d2639439df06a704ef6e8adf2f2c6ccd75fec7e6bfc0973561526c0cc373a` |
| 57 | opened | Lasna | `0x377a43d85b85fe1eaa022efc2f6fde92582753ea4b4b5ae29b7ae691bbc21e99` |
| 57 | requested | Base Sepolia | `0x1f7ba94ebe3d8e8f8a3a90dc64b389490cb6736d00027aaf5480ed57751d2dbb` |
| 57 | posted | Base Sepolia | `0x3deefbb4b5e0afd5b50d788f451591e5ae7dcca10d2acf023366b447d6643dc1` |
| 57 | evaluated | Lasna | `0xe5015ccf58985599fac6e073f15eb451acbb00bb6ec536ca71d2053eb260d0e9` |
| 57 | noTrade | Lasna | `0xe5015ccf58985599fac6e073f15eb451acbb00bb6ec536ca71d2053eb260d0e9` |
| 58 | opened | Lasna | `0xd8478fc1bd70437dc01639e2b3fdc5c2deed96ae4cd9ca292dd7d174ec06f372` |
| 58 | requested | Base Sepolia | `0x3586d50dc0e969fcbd035e2a6c6e0fffd7ce1cb6fc7df4bd1de350508471ea0d` |
| 58 | posted | Base Sepolia | `0x4f7e308c12e4cc627261901a40d586498484d4d34358dc22f4a9779abefaf8c2` |
| 58 | evaluated | Lasna | `0xcdd349fe4eb94ef6f5f04db7ec3f4788ab90749f3020509b26372c50211ecfea` |
| 58 | noTrade | Lasna | `0xcdd349fe4eb94ef6f5f04db7ec3f4788ab90749f3020509b26372c50211ecfea` |
| 59 | opened | Lasna | `0xd77259b7ca8c9f1bbcecba37e567727d20a765f9f3fa87a24f30cddf7947a548` |
| 59 | requested | Base Sepolia | `0x81148b3a2aa935c2f35f52fd97062b7c5264194a7dc8488ebd3d9723723d1054` |
| 59 | posted | Base Sepolia | `0x326ef8800c4c3304090ad21ef34ba687710c4b56c42aa8e3eaa33029cfdbd696` |
| 59 | evaluated | Lasna | `0x91a03911052be26ac821764735e02622249c7504d6e42341369b10a6650d2cfa` |
| 59 | noTrade | Lasna | `0x91a03911052be26ac821764735e02622249c7504d6e42341369b10a6650d2cfa` |
| 60 | opened | Lasna | `0xf85879fc89b55e1000b2cb775542064de088bc1614af0ecf37407280387f0107` |
| 60 | requested | Base Sepolia | `0x6cbc019cae3430c88fdc4fdbb9d93924c568edac444227a6715e2523eb442351` |
| 60 | posted | Base Sepolia | `0x24de7e9c83342e93976764720466b0a69cae33951dceaf8fb621b00787c5960b` |
| 60 | evaluated | Lasna | `0x4672bc4da578a85b45855c041c3a5c11e0a64c3ca8e57ca56e9de37f9eae4e5f` |
| 60 | noTrade | Lasna | `0x4672bc4da578a85b45855c041c3a5c11e0a64c3ca8e57ca56e9de37f9eae4e5f` |
| 61 | opened | Lasna | `0x63171ac4824edace8e2497b2b8ed17c3304ec608aa5ec174cd9f633345f40b9e` |
| 61 | requested | Base Sepolia | `0x15ca4138a224f4fdad9f422deaf7fbce2fc41b595f3526aea8480bfa2f16535e` |
| 61 | posted | Base Sepolia | `0xa4b91f6381e0d8d8db6fed7c29e85c82b9c876ccaa08a45dd42353e4cc65a696` |
| 61 | evaluated | Lasna | `0x76c052dcc11eccfda620e1358a15caa1e8ebecd15ab6e931172fa129befd6cf2` |
| 61 | noTrade | Lasna | `0x76c052dcc11eccfda620e1358a15caa1e8ebecd15ab6e931172fa129befd6cf2` |
| 62 | opened | Lasna | `0xb8d532e4b3cc9b5610714872fee1d058c28e3e940b146273ec41a9b3ce8d9bab` |
| 62 | requested | Base Sepolia | `0x515d37c3d82ce79034410b9bfb6fa53cf75d95ee98ef055f717ca7ba19130212` |
| 62 | posted | Base Sepolia | `0x44786669df8b47c974b01073343d9797a8cc27d5ca8cd7fbecb2fa04ab4586e4` |
| 62 | evaluated | Lasna | `0x1989cd93aa099157f2f07e602dc3399a01c131ff161d9a9685eaa84681a76159` |
| 62 | noTrade | Lasna | `0x1989cd93aa099157f2f07e602dc3399a01c131ff161d9a9685eaa84681a76159` |
| 63 | opened | Lasna | `0x9d63d497c168f090ec9990ea4fba0322905afc75154ede595c2c4876de4f0a24` |
| 63 | requested | Base Sepolia | `0xc2faba85f984eda93abae936c32aaddae78031fed866aa43c68b863753dd8820` |
| 63 | posted | Base Sepolia | `0xb3f477e90ef7133668fc001d5a820f99ae6a8e7d0723fa0fcdac34186731359c` |
| 63 | evaluated | Lasna | `0x12c7b898efea0c3fc41820b0887c2f7c37e02c75180d0cde9c18039e996869b2` |
| 63 | noTrade | Lasna | `0x12c7b898efea0c3fc41820b0887c2f7c37e02c75180d0cde9c18039e996869b2` |
| 64 | opened | Lasna | `0x455b46363838de0025ef6a882de9d4def80f5c8e068e956bc9ec9a04eda0bf4c` |
| 64 | requested | Base Sepolia | `0x6c9b0ae68dc1a49bb971a0b32b86fc4b84984e9eb7ae40f0a8a6e11f0a96f27f` |
| 64 | posted | Base Sepolia | `0xe06365bd0357f946f5b3946ae3d288d0a310b9228847b77d71ad2b0467ab65ee` |
| 64 | evaluated | Lasna | `0x20b11c63578ebb0efe17c0e690b2ca29afea75171348540fb6509f3b75cd0c9d` |
| 64 | noTrade | Lasna | `0x20b11c63578ebb0efe17c0e690b2ca29afea75171348540fb6509f3b75cd0c9d` |
| 65 | opened | Lasna | `0x94642d44f63bfd395f5f037326562bb24cfdbd32c8e1dce83cf6ca756eb48be7` |
| 65 | requested | Base Sepolia | `0xda41a0a7bf27432fbfc26a885ac43c66753042760fc26d540317119dc970fc24` |
| 65 | posted | Base Sepolia | `0x89ee858fe8ca397ce914659e46408431ec29a8214f4cb0bc33abe2d8946778b4` |
| 65 | evaluated | Lasna | `0x5430ab79ae2692d8b11bf8020f287fb8246dbf6041d7fe1276b98d4eb7a7333c` |
| 65 | noTrade | Lasna | `0x5430ab79ae2692d8b11bf8020f287fb8246dbf6041d7fe1276b98d4eb7a7333c` |
| 66 | opened | Lasna | `0xda6adf4c3cd722345232fd6fffe253d9b09d9e2c8404dc9b376d62ea28437765` |
| 66 | requested | Base Sepolia | `0x1699f36de9b5a67f347dcfc6f022ff1b54e43f4b43b48c64a3ffb39c7427619a` |
| 67 | opened | Lasna | `0x76140115760d31932a5c17d888cd952bdc9e28fa8d5aaa88a91a27d1abdd70db` |
| 67 | requested | Base Sepolia | `0x22ba6c6db6482e55225c5e4ed9799091d53df86e62ee78f99c18b955c6396329` |
| 68 | opened | Lasna | `0x7a54a4ab1cba41d84b037986c467dc0638b6b5479c4acfad9f91c8183030f08b` |
| 68 | requested | Base Sepolia | `0xc4aecc15f0ee9dca728182a16b87be2a4ef247bb19f4e2563e27899535bc683d` |
| 69 | opened | Lasna | `0x213022b7ed1062f1cd89b84e31d188b5f68faa728d81c8ff0b9995f282a4a1e1` |
| 69 | requested | Base Sepolia | `0xd1b25cc7c60b3ccc488ea4cc717ada07afd7d4b31677f2fdd394bdf0426063d9` |
| 70 | opened | Lasna | `0x7bffcdf5fea708c958f6d0b2ec107b4fa62d3699c66a9315e9248c5a91023556` |
| 70 | requested | Base Sepolia | `0xc9e65b20cf21e89c065e358d746f37d63d866e30999f3c005b95629093fabf99` |
| 71 | opened | Lasna | `0xb8780d2c676e905c2f5ab1f8eda283fbb0d67a360f695bee2fd16ec03b18a2fa` |
| 71 | requested | Base Sepolia | `0xdfefc5898c23ff15741e3d6a44ea8779496cf25d20bab7481d8959d6785af694` |
| 72 | opened | Lasna | `0xbc7c994541aba2eb44596dc12bafeff05297e6dc08b8eaad8a20b804d49a2734` |
| 72 | requested | Base Sepolia | `0x05545c1c54bb05a4ea0759d6aa8e00b052dd60e6b6629abfd23d62c02c3af8b3` |
| 73 | opened | Lasna | `0xb10e8dc91cbaefa25298d0641516fd34ad91dcc8a9d7edef4466b6adb7d8141e` |
| 73 | requested | Base Sepolia | `0xa430f2b0e05ab3f4743e0e0caee6aafa6a05bd3d9edb9f48ae80e80f5cb3eb4a` |
| 74 | opened | Lasna | `0x84084b20b9f01eb83b22782ff1899c947398a12727997b5ef1261a301f9cd9db` |
| 74 | requested | Base Sepolia | `0x4c8f702d897cdf9a556705874b2fadc2ea3e6ebf5c82b27043f128dcb4c068dc` |
| 75 | opened | Lasna | `0x1bec47d3e162b63fcef58882b915076c1e6b24b41e293ff9a20e24e5ee12abe4` |
| 75 | requested | Base Sepolia | `0x0d4fc59d3a0ad853858223038cb18cd7ecf8b02310641ea609d8948f1b693f9b` |
| 76 | opened | Lasna | `0x6aa2e6e5bbc03eef50a5869bb3c08e30f704ab646de0907970e3a725ed2f6bd4` |
| 76 | requested | Base Sepolia | `0xf5b2dbf4efbefa0785b3d1074bd5a1624eb5a0c2aef8dd0e9d792378d7d94f08` |
| 76 | posted | Base Sepolia | `0xd80d1a745c65406d090446fbee18e92fc53a03dd9a8ee9adffc3a168a0290f2a` |
| 76 | evaluated | Lasna | `0x5c9d97a141c59b8754d5c0bb333a7c8e2cbd7c3afda045a172a6ea40067715aa` |
| 76 | noTrade | Lasna | `0x5c9d97a141c59b8754d5c0bb333a7c8e2cbd7c3afda045a172a6ea40067715aa` |
| 77 | opened | Lasna | `0xcd74d059a102c7278d2c5427660cfa384c459e82b308a774fd3d1950edc812bb` |
| 77 | requested | Base Sepolia | `0xe8af460b5b718d653d6ae47a7b9afce8beee4abe91d065abd63eded44f0b1e6a` |
| 77 | posted | Base Sepolia | `0xb0c408903fea9576a4d226301435f1b3c5f50507e3794b0f1ae47d0571e53299` |
| 77 | evaluated | Lasna | `0x96b0b5545136a909d7e6c427a4c8589388b80d5c5cc14ac912747f85ac5463a5` |
| 77 | noTrade | Lasna | `0x96b0b5545136a909d7e6c427a4c8589388b80d5c5cc14ac912747f85ac5463a5` |
| 78 | opened | Lasna | `0xc92a9280d96ac34433378ca0015517a7aa26ad5b6b155f7d774dfe30f8d4a172` |
| 78 | requested | Base Sepolia | `0xfae645dbf6877fbdf50bebcaf6654020ca830f01069c3d203f09bc289d41da61` |
| 78 | posted | Base Sepolia | `0xe72e652822ee95ca379df2be4f83ac4347d68738b49760c6874d3666f36e363a` |
| 78 | evaluated | Lasna | `0xab8fde9b6f6bf94630ae89e45f96c069bfea588a9389ea1d5422d61991885910` |
| 78 | noTrade | Lasna | `0xab8fde9b6f6bf94630ae89e45f96c069bfea588a9389ea1d5422d61991885910` |
| 79 | opened | Lasna | `0xd9e5d2fc01457e17c97ee6d361e5f58cfdb1e15a086575fa8298247a7ef8141c` |
| 79 | requested | Base Sepolia | `0x1ca91f85dd6705ed8b46d63ca9217f5a763171905b3d81a33b2c54b0efa95e43` |
| 79 | posted | Base Sepolia | `0x596f272ef996b1f4f265cc3900c13ffb00d878b6e2520971d0a637075b9144a8` |
| 79 | evaluated | Lasna | `0xf6152559d27e1110d5be28bc672748ffcbbb4e2534790db2c30247f7564b09f3` |
| 79 | noTrade | Lasna | `0xf6152559d27e1110d5be28bc672748ffcbbb4e2534790db2c30247f7564b09f3` |
| 80 | opened | Lasna | `0x7c53ca680104e43a610dd4a652d7614231b8add4fbf443fe166ec8f380a43180` |
| 80 | requested | Base Sepolia | `0xff6d3f8b7d53140f865db38c2565f09cee599bd1cb37562f35c635bf25840c0a` |
| 80 | posted | Base Sepolia | `0x8174f8e210ec7b205fe9e1c0886d335cb00a88a7bde8b800f0223890f09c60b9` |
| 80 | evaluated | Lasna | `0xaad645062602f52b1d5549b1b6352283deb463bc6309932602e335094c79de07` |
| 80 | noTrade | Lasna | `0xaad645062602f52b1d5549b1b6352283deb463bc6309932602e335094c79de07` |
| 81 | opened | Lasna | `0xbafb27e4414ec41ed19c1b77680839b098e4176e2425580e3e9ed611007eb252` |
| 81 | requested | Base Sepolia | `0xd52630b2afd12211b5fe3d81d3fde5e57cd31431badb1ce67d6187c66fba85de` |
| 81 | posted | Base Sepolia | `0x727797abed49903c92fe17936f6dfced473e09dca160cab20396ec3d26c723ca` |
| 81 | evaluated | Lasna | `0x2205be299279614cf0c977bff2ee85290eafd42ff60ba6b10a65fe809438ade1` |
| 81 | noTrade | Lasna | `0x2205be299279614cf0c977bff2ee85290eafd42ff60ba6b10a65fe809438ade1` |
| 82 | opened | Lasna | `0x0a0d6b265a70b8d379e0c6d952ebb6d17e97e2a006017c2e2ceea702c8b1698b` |
| 82 | requested | Base Sepolia | `0x8c3441ea52a9e16c8aff52c5e38b1bdb8cb604abbda8ab93e5b5832d797a0b90` |
| 82 | posted | Base Sepolia | `0xe491f6965537d0dbe094ce5ffa6897d02516094b16f233fac8cd9aa913d8f54a` |
| 82 | evaluated | Lasna | `0x6ab9ca861d92e08336d0060519de936163bbd2c0f0e98caa7329a8ab48d4a0f1` |
| 82 | noTrade | Lasna | `0x6ab9ca861d92e08336d0060519de936163bbd2c0f0e98caa7329a8ab48d4a0f1` |
| 83 | opened | Lasna | `0x0ff1633a5f6b7b76748b8ac0597e1f31f6a5466f56b586889699ad44b92e068a` |
| 83 | requested | Base Sepolia | `0xdc853065db7bc07e979cc4661ac636188835f0082dc5ba923ecc266c3749b1af` |
| 83 | posted | Base Sepolia | `0xf255e16f0fa811cf7b9f18c5432fd3d1d9ece51dfd24061cd14e56c67f45c33b` |
| 83 | evaluated | Lasna | `0xc364c4c608cdde62c3bfd7a17dd83e22f05586aae8bfade61dd17c7bf5a0ec20` |
| 83 | noTrade | Lasna | `0xc364c4c608cdde62c3bfd7a17dd83e22f05586aae8bfade61dd17c7bf5a0ec20` |
| 84 | opened | Lasna | `0x6e2218dc0498ed140a7338925db398dece765835218f0706c43e0251771f3592` |
| 84 | requested | Base Sepolia | `0x9c9012f645bfb63551e8d8474d69dbade24c767e9f7098df5fd64f1ff2b55269` |
| 84 | posted | Base Sepolia | `0x461a7aa35c3d3ce16cab04a88d5a37b546f3334082ecb7829b66b8259805129e` |
| 84 | evaluated | Lasna | `0x9086f6cbe11ec9b496f8f259e7cbf4eb54c509bfac7e513d3cd69415a811b5c4` |
| 84 | noTrade | Lasna | `0x9086f6cbe11ec9b496f8f259e7cbf4eb54c509bfac7e513d3cd69415a811b5c4` |
| 85 | opened | Lasna | `0xacf7dda6717d14434f034ccb243c2ea25fedc0d3154ed88728aa4b12a80975ce` |
| 85 | requested | Base Sepolia | `0xfd53bb252d414a4e22f101fd5ce9a3647af7550ccca22d21399d3bb1ec98ea75` |
| 85 | posted | Base Sepolia | `0x12d670b1f2fa4df7b671006d580a872872aeceef11890b69c1bdfcc7724110fe` |
| 85 | evaluated | Lasna | `0xa6ec9bcf8454f16e974202d8bb3788fe7663e06c724308d597144d5e353f3c26` |
| 85 | noTrade | Lasna | `0xa6ec9bcf8454f16e974202d8bb3788fe7663e06c724308d597144d5e353f3c26` |
| 86 | opened | Lasna | `0x0372f6a93285338fbe2796796671aecff6140e85d02e3a70aef552245a609f51` |
| 86 | requested | Base Sepolia | `0xe7f445b0961b2d95ed4a1859815409b1f54f6f10774499e84e530ad5f3bf9b99` |
| 86 | posted | Base Sepolia | `0x9b1cdaeb0f6eb7ddb1e1f1f6607c8ee0f0858ab197bca77a7d29f0f87f933e8a` |
| 86 | evaluated | Lasna | `0x70be8dfc001e6d6bb10c626586ff688a8662452043f163f3000b1a4634d37200` |
| 86 | noTrade | Lasna | `0x70be8dfc001e6d6bb10c626586ff688a8662452043f163f3000b1a4634d37200` |
| 87 | opened | Lasna | `0xdff458d91a9faa4d1f466de151c80a5c46df672072d8d585597a228c7ba848d9` |
| 87 | requested | Base Sepolia | `0x68ce82ede35cf80b3e58354090736f35c063d6b69a619ad6ae16fd9fd012c87f` |
| 87 | posted | Base Sepolia | `0x2ad14c622a43a3e40c73cec5606f29b10f1f7183fc91c33395f427a3bca389ce` |
| 87 | evaluated | Lasna | `0xa0ebb8fb6ccba9b14340588b4aa554bc4a2bde1fdf9f0015ae00e2f3c67d2125` |
| 87 | noTrade | Lasna | `0xa0ebb8fb6ccba9b14340588b4aa554bc4a2bde1fdf9f0015ae00e2f3c67d2125` |
| 88 | opened | Lasna | `0x747d0caa7ff20bffea4054986bab4790397ebde96eaa467ed6296b3139f72cb2` |
| 88 | requested | Base Sepolia | `0x96401850242386a94195066dd52c018d0e9d7c2cf170d680dba8b69c9c98924b` |
| 88 | posted | Base Sepolia | `0x41a479621322a456ea0b1494d8ef0222315b2f018a197f23da70a5b3d1ad0e57` |
| 88 | evaluated | Lasna | `0xa152be79ece9c86ac580600a980366ccc469149acf86a62edd4a6086f1c23058` |
| 88 | noTrade | Lasna | `0xa152be79ece9c86ac580600a980366ccc469149acf86a62edd4a6086f1c23058` |
| 89 | opened | Lasna | `0x00b567517ec2aab061f6bbd8c35208c908c9d198796f885d3d986dee9c4d3640` |
| 89 | requested | Base Sepolia | `0xc79fb29e006cb1dcda8f124e8b6b52aa2581f7dcfe77b418897739bb76e11c82` |
| 89 | posted | Base Sepolia | `0xda8ccbcaa69d322e0fae4cd02664b1ebf0dc68e4d7f5911e15a380043a51d2c1` |
| 89 | evaluated | Lasna | `0x8d10e910eef6b8dd833ad80252de8d82504fb7f73019722dba6e01ca1e4447c1` |
| 89 | noTrade | Lasna | `0x8d10e910eef6b8dd833ad80252de8d82504fb7f73019722dba6e01ca1e4447c1` |
| 90 | opened | Lasna | `0x0ff415a0247c556a2ac15dfbd718ba4d73fbd8327ae71b655d907fa70e7c251c` |
| 90 | requested | Base Sepolia | `0xcc9dfa4a6a3cf827e9619052ccaca3112f7166f73577dcd781cf25c15ea3dcb9` |
| 90 | posted | Base Sepolia | `0xce5f02431b60860e1526435009acb17055a0ac25a99004ff71eba6f3012b3e9a` |
| 90 | evaluated | Lasna | `0xc90fabdbde155430223692e887c95760f4f96c6704e0d096c50ca012f6e5281c` |
| 90 | noTrade | Lasna | `0xc90fabdbde155430223692e887c95760f4f96c6704e0d096c50ca012f6e5281c` |
| 91 | opened | Lasna | `0x27737cbfee1df81a974b35869914f92cec7fa3a1390a67f54af8cd93702f83dd` |
| 91 | requested | Base Sepolia | `0x7459f58cc2ae36ff9cd2587486e86265e6af0cd392f5939e675eebf6b26d53f1` |
| 91 | posted | Base Sepolia | `0x69a419344126c55148b0acf2ed34653986d1b5d6eb2ebb4d81abb4ed07fc9a6a` |
| 91 | evaluated | Lasna | `0x81bcedb69db0173926de3c593d8b1f7e6e0f55e822542ee75b5277782fa41b61` |
| 91 | noTrade | Lasna | `0x81bcedb69db0173926de3c593d8b1f7e6e0f55e822542ee75b5277782fa41b61` |
| 92 | opened | Lasna | `0x97d6fb1410af75568d54dd443e45110bef398f248edf71225b8c388e6b4e525f` |
| 92 | requested | Base Sepolia | `0x0ffdbe3b7d9c2a07ef77a5634dd1bcbd094176622dfcdafb3d318e60cb6759df` |
| 92 | posted | Base Sepolia | `0x2f17072d3789556bd6734cbf194aa8c94cd7ef4351eeacff24e2a3539222aa50` |
| 92 | evaluated | Lasna | `0x9e2e0cf7f830596e8e5375ee4b5cb44adcdf42be65ad01effadefa18358ef27f` |
| 92 | noTrade | Lasna | `0x9e2e0cf7f830596e8e5375ee4b5cb44adcdf42be65ad01effadefa18358ef27f` |
| 93 | opened | Lasna | `0x09ac726bd7959163961fb8a10943753a660a6c2d4a0a08713c27948725d769ab` |
| 93 | requested | Base Sepolia | `0xda46cc31de56e728c41bcabaef01c551187d302c8e78c6a0182ff6edf4e68337` |
| 93 | posted | Base Sepolia | `0x191a1cc52270f593233bef2c0b531ef1c29a8c067d3828fa65c8bf6622f1808c` |
| 93 | evaluated | Lasna | `0x7562ad562879d5cb01651b941475d978e00bf327acda647ba71dd632d5f9f61c` |
| 93 | noTrade | Lasna | `0x7562ad562879d5cb01651b941475d978e00bf327acda647ba71dd632d5f9f61c` |
| 94 | opened | Lasna | `0x23f2f8b2671eb0b0f4d55fe0577abc6ddb819216a153a38785e61fabb971d379` |
| 94 | requested | Base Sepolia | `0x26118139dea09a6fd728b797082e92398a3140c092c5da9f9c6373ac97c23513` |
| 94 | posted | Base Sepolia | `0xc9e85a8c680e995e57b26b94f461312e14d50e4d0926f27a59673749559e0478` |
| 94 | evaluated | Lasna | `0x5a8cd9c90015a2011d858a0df0742f3773f09388e61ca13353dcf74c15542998` |
| 94 | noTrade | Lasna | `0x5a8cd9c90015a2011d858a0df0742f3773f09388e61ca13353dcf74c15542998` |
| 95 | opened | Lasna | `0xf3ca2b1b682afad6b842cd4b16d9e15ecfc9493d88fb778702556f9153d3c72b` |
| 95 | requested | Base Sepolia | `0x852ff8cd4f05dd1ae6adda224f1dfd165c9c1bba2f18d619ffd7419227eaf354` |
| 95 | posted | Base Sepolia | `0xd0da4db7266589af94797da918865ee781327624635061c5504a5e7f577ab80f` |
| 95 | evaluated | Lasna | `0x42690adfb2c05cc5fac5a628ab6860d80c0e20165072d0c011e8376972060ef4` |
| 95 | noTrade | Lasna | `0x42690adfb2c05cc5fac5a628ab6860d80c0e20165072d0c011e8376972060ef4` |
| 96 | opened | Lasna | `0xda8a0ab7a35fe20f882fe5f4238e92a8fa70ee2de162df14e4045ede6ce981c7` |
| 96 | requested | Base Sepolia | `0xc8c344dea432e9ecf80da5e0a32a3382d3ea7081db92541a0f648f7a6cd774c9` |
| 96 | posted | Base Sepolia | `0xec25e4a710cbdc0fe32507faf9385ba46a5eec5ced00c64bc1ba69223b8ffa97` |
| 96 | evaluated | Lasna | `0xe7314ce5ef0b0512a6621e9293364dd3c1526d88bf111ec3486bcd14cee25fd6` |
| 96 | noTrade | Lasna | `0xe7314ce5ef0b0512a6621e9293364dd3c1526d88bf111ec3486bcd14cee25fd6` |
| 97 | opened | Lasna | `0xb94bbbcd60793127626ded7a451ac39ccb7a0a3a11dbf1586ceb04a7bb764193` |
| 97 | requested | Base Sepolia | `0xcee36f5050d38de6b5ae333a2251c516ceb5dd6187a8b1d75a0ce72165ab2423` |
| 97 | posted | Base Sepolia | `0x08dc5b6781ecaffd34bc8b93f11ed2dbc9f5f49908bcaccdd4cd6c07656d2f58` |
| 97 | evaluated | Lasna | `0x7a5940f603307728c646a3e34223be9e3cf736c8f4888a60cb2e48622b8916f7` |
| 97 | noTrade | Lasna | `0x7a5940f603307728c646a3e34223be9e3cf736c8f4888a60cb2e48622b8916f7` |
| 98 | opened | Lasna | `0x123a20b5aae09a4ba65a626c58db904715cb54a1ac15368fbc65e381f27faa91` |
| 98 | requested | Base Sepolia | `0xd22f660841a4c1cf1dda6f5ed7da9734f7d5b4609091f8dbd111d865d9027d02` |
| 98 | posted | Base Sepolia | `0xbf994bdce97d1b550ebfa5001bc74d9f8a47d5b384963b44ae4c00cd964fb329` |
| 98 | evaluated | Lasna | `0xb277598d1cbbd0a36cbb9f4c068a7f30ed12fc53957371d8a0408e2204e7699d` |
| 98 | noTrade | Lasna | `0xb277598d1cbbd0a36cbb9f4c068a7f30ed12fc53957371d8a0408e2204e7699d` |
| 99 | opened | Lasna | `0xffc42fcf7a5dfdb762ce5fc75b0cdc075c8762b011002493011046595546c07d` |
| 99 | requested | Base Sepolia | `0x8aa00eef03bd0be5315c863c51b4dcf11c9c51852c09a90ba9b286d9ce80a498` |
| 99 | posted | Base Sepolia | `0xd41d43b06d721bef62de01e5051f2300eed08326f14edbf187c904617ca72645` |
| 99 | evaluated | Lasna | `0x98305f9fcc7d73d573392263ca0bace8774713f3ea7c480b15ef62764563377d` |
| 99 | noTrade | Lasna | `0x98305f9fcc7d73d573392263ca0bace8774713f3ea7c480b15ef62764563377d` |
| 100 | opened | Lasna | `0x9dab28b112bfaa0a58e9de78f474c14bc671e2ccb433000ed6a7813f5d1ce3a9` |
| 100 | requested | Base Sepolia | `0x0ecb5f346e0ed119262e5f7605e24ba7aac581e5a34dd308e6eea7c8edd414fa` |
| 100 | posted | Base Sepolia | `0x12d8db10454d9f43690d5106338cca96bfc8fe32f6db4a6407ad033cffc6fb6a` |
| 100 | evaluated | Lasna | `0x2db4d0c5ea522ead1ce39899e65681d0d46192a5d0bab5013e78e13c06cb4e22` |
| 100 | noTrade | Lasna | `0x2db4d0c5ea522ead1ce39899e65681d0d46192a5d0bab5013e78e13c06cb4e22` |
| 101 | opened | Lasna | `0x50b3ede747afb52e6ef352d9c2eea73d9144f3087aaa003a4fe6e4dad9b0e347` |
| 101 | requested | Base Sepolia | `0xae37fce254256dd392f5b5fb17a98ac1ab0274203e88e3f1fbd8f051f7b7311c` |
| 101 | posted | Base Sepolia | `0xfb5539681ad00134368c07c6c14980475258e73f27c5eafe2386d3a26ba563d8` |
| 101 | evaluated | Lasna | `0x46f43d62ff188d207b55fe4f86014150c4c3fbd6c19a50fe6e4cfe150fc903d6` |
| 101 | noTrade | Lasna | `0x46f43d62ff188d207b55fe4f86014150c4c3fbd6c19a50fe6e4cfe150fc903d6` |
| 102 | opened | Lasna | `0x43afbe8618a1cc3a2c4de26c6f594646cf05cffc9d495901a4c662a3c61312cb` |
| 102 | requested | Base Sepolia | `0x0c60e2ccc39fcaf46d105af2ccab62566163c7b98ed3ce51f1b55a8b68bf5992` |
| 102 | posted | Base Sepolia | `0x4cdee9a0bb1d73ee64a0b2b704758e8f81b2f0aea3aa10cadcb47a9c4156fb98` |
| 102 | evaluated | Lasna | `0xcc3188d7f844df38779b19fdfefa344cc4253ab6b3c1bf5663b76bc22a7be891` |
| 102 | noTrade | Lasna | `0xcc3188d7f844df38779b19fdfefa344cc4253ab6b3c1bf5663b76bc22a7be891` |
| 103 | opened | Lasna | `0xfb65df7e48840fa30092501b3cdde9b07a3d0a01a2fbeab9f0cf2bec3cba795b` |
| 103 | requested | Base Sepolia | `0x8cbc6d0dc45de15f339fe961027cbf5282303c40aa69dde59b4aeccf95a35e17` |
| 103 | posted | Base Sepolia | `0x944700573ba21388c216d1cfbc303a13b1eb7cbd910f695975d73e9b8feeba15` |
| 103 | evaluated | Lasna | `0x7738486bf7ce0c193ec46c9ba9b11ddad203b273d8fa4eb73a3d0a85cc1b1796` |
| 103 | noTrade | Lasna | `0x7738486bf7ce0c193ec46c9ba9b11ddad203b273d8fa4eb73a3d0a85cc1b1796` |
| 104 | opened | Lasna | `0x11906e671c338789d0be968addbe9d6b94c5642ebd8968e554df5a15748fce86` |
| 104 | requested | Base Sepolia | `0x3ddd0f80c11ae37f21d7ce47f6f1381b6b5a61c8aca96f6b7f29fb21d1c80474` |
| 104 | posted | Base Sepolia | `0x5b6a65a76bd900be09c52abd3e334156a7172f5d2f7fd816161a4253dbde6b2e` |
| 104 | evaluated | Lasna | `0xb6899b022d607ccfc5a9e54ae500154175a39c6de79f7d8a159c310e43342606` |
| 104 | noTrade | Lasna | `0xb6899b022d607ccfc5a9e54ae500154175a39c6de79f7d8a159c310e43342606` |
| 105 | opened | Lasna | `0x37044dd5d01fe334a04e400fac6c864312f76481bea1b4a14b18b2a63d32ca21` |
| 105 | requested | Base Sepolia | `0x955f2c42fd57483099a47c419583de17a53dd0ed7fe3e2f514be756ee5f307bd` |
| 105 | posted | Base Sepolia | `0x486a470d9e03351a09aca634414d95207eeec012149874d3bc7cdf39122d6746` |
| 105 | evaluated | Lasna | `0xad39f20b2ed8e367dcda31e20a0e88eee575e59aab16ba49941bd0bcc6b2beea` |
| 105 | noTrade | Lasna | `0xad39f20b2ed8e367dcda31e20a0e88eee575e59aab16ba49941bd0bcc6b2beea` |
| 106 | opened | Lasna | `0x436c9908ee66150e9831f588364a8754784f149dcb71e0f620b59eeecfe9b4c9` |
| 106 | requested | Base Sepolia | `0x0aee5bcea6868d3b354cb930c8378b488ba90f4e6ed3bbbdb69da3ce060f3888` |
| 106 | posted | Base Sepolia | `0xe5858e5b2c07883d9fe96899570a9a703bd8aace7c4b863c820ad59c02da0f01` |
| 106 | evaluated | Lasna | `0xe64ca36f8fe47eb1989755f8dbd228cdb2b53cfda9a9af9aac42ad1ead4a6c83` |
| 106 | noTrade | Lasna | `0xe64ca36f8fe47eb1989755f8dbd228cdb2b53cfda9a9af9aac42ad1ead4a6c83` |
| 107 | opened | Lasna | `0xf7ba8b132583e03258b4085f971f8f14e02ae607c3cfa0d849579b071d54b84b` |
| 107 | requested | Base Sepolia | `0xab972801fee95c1fd35a2384862e548648b6c0d4fad354b8b4711fd14815ef02` |
| 107 | posted | Base Sepolia | `0x11d6b0cf4201a373f31237e131977635d58572002e6a541c1191d3a98416ac2e` |
| 107 | evaluated | Lasna | `0x5c247842e522e6b21bbfe4a73248fb137693f543cb29256551f65e87c310633c` |
| 107 | noTrade | Lasna | `0x5c247842e522e6b21bbfe4a73248fb137693f543cb29256551f65e87c310633c` |
| 108 | opened | Lasna | `0xb1c62462b580ec7b101bcc354c1539ea28703c12ce3da4f46c84dba460f4b84b` |
| 108 | requested | Base Sepolia | `0x0978092e740e2775c02383e7c6424d0d2e26a681fc9cb284da50139a1e72f022` |
| 108 | posted | Base Sepolia | `0xe2a8a5d7559e607e1bf184c91eab77390a81f234a10fcf262f0cef28e893c70c` |
| 108 | evaluated | Lasna | `0xb3f95d0b2f341af65bb3d5c61f3aa594755276c7475d00cdde8eddc8cb0596cf` |
| 108 | noTrade | Lasna | `0xb3f95d0b2f341af65bb3d5c61f3aa594755276c7475d00cdde8eddc8cb0596cf` |
| 109 | opened | Lasna | `0x0bf5f1e42c15f046a4534c0928a6499c99d928983bb64362b7d19ac8e878dabe` |
| 109 | requested | Base Sepolia | `0xd8771dcee5365f84fbd4eeb5be1536a08f10053638755b427f3cdf57f5a2eaec` |
| 109 | posted | Base Sepolia | `0x4dfaa3867d2b1435ae52e83ab22109699a2d20ff68a07a52afb06332d444d740` |
| 109 | evaluated | Lasna | `0xedb917555ae21fb603906132255c8ac6b49a455e7acdafe4fe7852a221dd107d` |
| 109 | noTrade | Lasna | `0xedb917555ae21fb603906132255c8ac6b49a455e7acdafe4fe7852a221dd107d` |
| 110 | opened | Lasna | `0x840301ce23c19232e9bf1015200951c2600ec7008a0f8af8194d82fef1b52d3e` |
| 110 | requested | Base Sepolia | `0x25ed4e1293e50a460892ddc85022013a0a0540add32a311a84c95eebb2d8f558` |
| 110 | posted | Base Sepolia | `0x082dc5c3b039b1fbbe042f4b5033739062a66501a3c61e67c006b4fd110079a9` |
| 110 | evaluated | Lasna | `0x72b7eea833452359d110c407c66979108fb60ad1a92100231b8abfed5c13f518` |
| 110 | noTrade | Lasna | `0x72b7eea833452359d110c407c66979108fb60ad1a92100231b8abfed5c13f518` |
| 111 | opened | Lasna | `0xbf5735655d7c522a6ec0e1a9ba88e64aac8604b665f0717bc0eab747c5727993` |
| 111 | requested | Base Sepolia | `0x0a6ce7b71e165af0f6e86c6db62bba9275bc0ca919a097f7df124e8769fb764f` |
| 111 | posted | Base Sepolia | `0xcc5619abd3eea3da2fa2140192f5fba70756a71c280f275564c5ca4268b029ad` |
| 111 | evaluated | Lasna | `0x7458ffad45e4874db90a13839067c978663006875c9ed46c3ea4d2e05002beab` |
| 111 | noTrade | Lasna | `0x7458ffad45e4874db90a13839067c978663006875c9ed46c3ea4d2e05002beab` |
| 112 | opened | Lasna | `0x435dd1adadc3f7211475093441168647eb1580cdf1e126ca08bf8e89c8d167f1` |
| 112 | requested | Base Sepolia | `0xe0f9903e6f450771b7d695911632cb40872e11a54a48e9559bdc14de48dd7749` |
| 112 | posted | Base Sepolia | `0x330bcd8df2a8c00bf4d20d5a5f99eb03d581de02891939f0fc45f06804f5837f` |
| 112 | evaluated | Lasna | `0x745e7e0a0b573117c6118fe528edeebcb87945217f53002a751bf786af61b4c7` |
| 112 | noTrade | Lasna | `0x745e7e0a0b573117c6118fe528edeebcb87945217f53002a751bf786af61b4c7` |
| 113 | opened | Lasna | `0x92c3bd0e5585d13b008c9de878f30a4300c0b82318955b50a8e71c627018cf71` |
| 113 | requested | Base Sepolia | `0x90f4b101b42ee411a6b8b5df5f79da42e384665f85e8d79899d49f70e27a108e` |
| 113 | posted | Base Sepolia | `0xb1063475999beeac9b659e2e5b65554ad4e1350b4b2b2c18ed9518cf590cd66a` |
| 113 | evaluated | Lasna | `0x65e71639b49f5797bdc1d802d427d8ca3ec537c47b01dca283fd5ce34088b69c` |
| 113 | noTrade | Lasna | `0x65e71639b49f5797bdc1d802d427d8ca3ec537c47b01dca283fd5ce34088b69c` |
| 114 | opened | Lasna | `0x98c376c5e4621c7d28f4a9719243d6e6e8701074c7b17599d0d2323b22a6dc31` |
| 114 | requested | Base Sepolia | `0x00e230c48fecfb412f9469234b831df50b92e0a8cba293d629f1a4d3d909be54` |
| 114 | posted | Base Sepolia | `0xee465b3bf4b92cc602eabb1313410df0c04d87153cb2587a1040d84916584cbb` |
| 114 | evaluated | Lasna | `0x8cc1503353f08fe81c38a440ddceab3cc1b8c1ce3c7a4caa730a9cb860f291e9` |
| 114 | noTrade | Lasna | `0x8cc1503353f08fe81c38a440ddceab3cc1b8c1ce3c7a4caa730a9cb860f291e9` |
| 115 | opened | Lasna | `0xd7ae959cca10a5a97dfc7a86d458ce7f7e4ca1b5b9acb968ea854eee6749ed7f` |
| 115 | requested | Base Sepolia | `0x6beb2b3c74868c26ea8be8e2b77f655f55cdc110146820bc9ce4a335cf848e52` |
| 115 | posted | Base Sepolia | `0x29feed5f120adc024a8d7bb6ba5136b91c80121ab1223c4d3fc824876ff2a571` |
| 115 | evaluated | Lasna | `0x3c687c8f53bd7cb5a1222c690c2473367528548b192e5c87b4acf306c7fc8f4e` |
| 115 | noTrade | Lasna | `0x3c687c8f53bd7cb5a1222c690c2473367528548b192e5c87b4acf306c7fc8f4e` |
| 116 | opened | Lasna | `0x36b994408c63ba899219aaa162df0e16934661b11a46f7cfc9b63c127b21b1d1` |
| 116 | requested | Base Sepolia | `0xbd4d8eed1e68e27e4b48773c4cc880dde19cc28aad8039e9078639c6567b7c04` |
| 116 | posted | Base Sepolia | `0xfbeac05d99e9b3367758c3bd26a7ef16d14e48e2a9161a8cb3b4583f2c441131` |
| 116 | evaluated | Lasna | `0xe6c11032d38055a286f7b640b41985d6754454bc477f73c1d2c5160a2fb56d94` |
| 116 | noTrade | Lasna | `0xe6c11032d38055a286f7b640b41985d6754454bc477f73c1d2c5160a2fb56d94` |
| 117 | opened | Lasna | `0x7375fcef2c5c6b1f006539786279e353b592c6352d2b64745d9b556d17147b48` |
| 117 | requested | Base Sepolia | `0x2e60d7f2117fdfe22fc9eb7ee33ac80cdf9553827517d27ecb500405dd8cb721` |
| 117 | posted | Base Sepolia | `0x2cd40bc8ca6953f61f8082e1b1e0c82619b731d1cfaf61c2a97cc6e7e19b04d3` |
| 117 | evaluated | Lasna | `0xbe9712d878a303159e3ea81424c2554a9e0abb0670b666e8582fa99a9c3d5e0d` |
| 117 | noTrade | Lasna | `0xbe9712d878a303159e3ea81424c2554a9e0abb0670b666e8582fa99a9c3d5e0d` |
| 118 | opened | Lasna | `0x1fa50c4ee27c68644e998e44358ef7a5f8856be13c39cb8dd33d394854794d9d` |
| 118 | requested | Base Sepolia | `0x546773c4ad39c79e972044657ff5918d0f8b65d195ec0856696f4b60808461f4` |
| 118 | posted | Base Sepolia | `0x6784f9e40c185e99c35e1a539af013564b164aea3f6b5b5fa2f02ee19711b109` |
| 118 | evaluated | Lasna | `0x46bb13b0e048ee666bac112a7f41f72fca005caa8235e2bd0acad7eccac3f0c4` |
| 118 | noTrade | Lasna | `0x46bb13b0e048ee666bac112a7f41f72fca005caa8235e2bd0acad7eccac3f0c4` |
| 119 | opened | Lasna | `0x9c9e317c952ccc7c575e1fb7a4f346bd2c9a1cc7af3569235ecc029d3fcc9d52` |
| 119 | requested | Base Sepolia | `0x17d74a33d8d83fa662c9ab20db58feaab35c7dc2b9925ef297f4aa3e0e69a791` |
| 119 | posted | Base Sepolia | `0xfa28774def50476d4988ba4f33769659884402449c2d8f9bbe927356b744445d` |
| 119 | evaluated | Lasna | `0x342942b99d21bef3a62fd51631208e6447d9c6bb01f8fd1f6f8966d6138f0305` |
| 119 | noTrade | Lasna | `0x342942b99d21bef3a62fd51631208e6447d9c6bb01f8fd1f6f8966d6138f0305` |
| 120 | opened | Lasna | `0x92aaf50cd9f6d9ea00b292f91a10927b3da25f8f6b6f2bac5516b35dd16fd400` |
| 120 | requested | Base Sepolia | `0x6137e88a71d8f1bbd7ad56e7a18478e3af5791523c98cc96c920daaba690c9fb` |
| 120 | posted | Base Sepolia | `0xc4c02d1ba8dc08a89e8c4794808217d23eb293808d1d18c443193152b7ed78ff` |
| 120 | evaluated | Lasna | `0xbeba631437f08b6f40b5eb1484674dbaf821f4c91a8a92d906048aefffa54a81` |
| 120 | noTrade | Lasna | `0xbeba631437f08b6f40b5eb1484674dbaf821f4c91a8a92d906048aefffa54a81` |
| 121 | opened | Lasna | `0x58020eeadd4d2ed5409d8370a103b7f9af8746387d6209e0c333f41dd4739502` |
| 121 | requested | Base Sepolia | `0xfa3b72f8b509c481f37c7f293719f88b9a7097f117dfa37e5577d8ec29e468ab` |
| 121 | posted | Base Sepolia | `0x3ade34114b2854ed666639384452d4658324fc8d994511f732ea76de1d9096f6` |
| 121 | evaluated | Lasna | `0xebf899b553397411384dcef7f1306e1720de15e485301a546c2da137c327f2c1` |
| 121 | noTrade | Lasna | `0xebf899b553397411384dcef7f1306e1720de15e485301a546c2da137c327f2c1` |
| 122 | opened | Lasna | `0x2875a4baa84018f03ff9ef5977088ac8071002e6788ba79d2df2563f88a1eddd` |
| 122 | requested | Base Sepolia | `0x29a94264af9f27155b37e44b1a8c54c568905034d7299465298a4f774204c5d0` |
| 122 | posted | Base Sepolia | `0x457c4f422c38a825901c3a1ab716bc812658389a4b53a754221cd9b16cadbd6f` |
| 122 | evaluated | Lasna | `0xda72916d525b4fa39602548fdcb8f38401e4e1463299204a1cb663fad233cad8` |
| 122 | noTrade | Lasna | `0xda72916d525b4fa39602548fdcb8f38401e4e1463299204a1cb663fad233cad8` |
| 123 | opened | Lasna | `0x650956d57b2c05d3fcaf3f449b99a5fb7cafee34cfdbb8ee7c1bde5d1e7c5396` |
| 123 | requested | Base Sepolia | `0xaa1b78ea6c47956ce1682bba4ef935887a4bf9068de93d98fe9c5057512df2d6` |
| 123 | posted | Base Sepolia | `0x7409b314f54e57e1aa3fdc3e695f24a555e10cebc3fe7c2348d47cd927f6d3aa` |
| 123 | evaluated | Lasna | `0x7bcf73364a9d4ace71f87f1d678fdee2848e03136ffbbb1619b981bec58b1685` |
| 123 | noTrade | Lasna | `0x7bcf73364a9d4ace71f87f1d678fdee2848e03136ffbbb1619b981bec58b1685` |
| 124 | opened | Lasna | `0x6fb38fe4e88995274935203be2c777ee5bdf7e16e3325272c5a02e7fa9e618b4` |
| 124 | requested | Base Sepolia | `0xb997acacf749e2bc1ebdbf496283efe00f09f4ec634e37455223025370edc9a4` |
| 124 | posted | Base Sepolia | `0x1724ce8277d970e29956d88b3504b1e3901218cf35ebf9d8729c0431db6cfe0c` |
| 124 | evaluated | Lasna | `0x43cda0a829bd54e449c085d0ec140e6359de978887127b7e73c8e8e815bbbacc` |
| 124 | noTrade | Lasna | `0x43cda0a829bd54e449c085d0ec140e6359de978887127b7e73c8e8e815bbbacc` |
| 125 | opened | Lasna | `0x3aee86383612969410be44cd421d9a83e92ee12505822f4cbfd59428ae3dfd3c` |
| 125 | requested | Base Sepolia | `0x9a0a62ac83ddfa5565eee258635464e5ffc959e9a550aac00f3b7b476e87ff91` |
| 125 | posted | Base Sepolia | `0xafbc5a956449ada39d73b41283413746f79793b26f6b4427b50162999bfbcb68` |
| 125 | evaluated | Lasna | `0x5253526d3a0ebb5aa9947b00cae1a9a1c8baca71fa913f73a2008a372b331eaf` |
| 125 | noTrade | Lasna | `0x5253526d3a0ebb5aa9947b00cae1a9a1c8baca71fa913f73a2008a372b331eaf` |
| 126 | opened | Lasna | `0xcdd87d41de3c6de0190920bd162284bf18782ffb09c2c754a9d1a8ff7aec611d` |
| 126 | requested | Base Sepolia | `0x00e9d942094e77cb1e68fb2466eee4825dad72e71d682628ef6cbf190d2e0aca` |
| 126 | posted | Base Sepolia | `0x61e82273a905fa38cfd71e0f9fa3ed7bfba2f7cff4e318f7d6e79d096f780a72` |
| 126 | evaluated | Lasna | `0x9b1b35e37a752128a882730a90e195c83e35bc184e890c9a2d8073f45f91f56f` |
| 126 | noTrade | Lasna | `0x9b1b35e37a752128a882730a90e195c83e35bc184e890c9a2d8073f45f91f56f` |
| 127 | opened | Lasna | `0xc39db3fede8009c2ff55d60023111b8ccaf83d3a05895726ea7ecbff2e88100f` |
| 127 | requested | Base Sepolia | `0xadbaa32f07133aa1dd586cd40c968ef0e4c06aa5693d882337d20a553340e54c` |
| 127 | posted | Base Sepolia | `0x75981332bfb73bb1fb81ecbac0861e9100a074c723fd22bb5f24f39685429276` |
| 127 | evaluated | Lasna | `0x5f5a150e7f5570e2d4359713b60b68f2e2313d988fbaaa1778217ed1aff963a2` |
| 127 | noTrade | Lasna | `0x5f5a150e7f5570e2d4359713b60b68f2e2313d988fbaaa1778217ed1aff963a2` |
| 128 | opened | Lasna | `0x6682d4a574e05e493ff5a582be9d03356f78958737aa4bc1e6ed43436c0935da` |
| 128 | requested | Base Sepolia | `0x66bc56199ec3fc0f35a8e01e8dd009ea01607c239dd649193a5ef9c10db52803` |
| 128 | posted | Base Sepolia | `0x1e6b485ec56b92bf8c5625b24da6efa364b726b4feebba2503b4668f62290f1c` |
| 128 | evaluated | Lasna | `0x42787d5eae566d3453cdab6c48fa787f647fe7d1364a0b898839e741c4f856e7` |
| 128 | noTrade | Lasna | `0x42787d5eae566d3453cdab6c48fa787f647fe7d1364a0b898839e741c4f856e7` |
| 129 | opened | Lasna | `0x220fbce245cd7dc67124248170a743593156a40ff8c9e7bbca9b9432cdb3a582` |
| 129 | requested | Base Sepolia | `0xa9bd961ee11090de72ae441bb44b60bb0e938431018a883d776e44fc17cbcb37` |
| 129 | posted | Base Sepolia | `0x40c79f92bd87fbfef57f38166a84533b0d5b6a4224d642499ffbb8be3f0e348e` |
| 129 | evaluated | Lasna | `0x60842cb6eadb9a36d043a0b0547d1ed22a0e9108dda80321d25475d41a6cceec` |
| 129 | noTrade | Lasna | `0x60842cb6eadb9a36d043a0b0547d1ed22a0e9108dda80321d25475d41a6cceec` |
| 130 | opened | Lasna | `0xde8cbb64ff9118afcc6ce4d87e203083334f512f933eeea6505d134736809286` |
| 130 | requested | Base Sepolia | `0xffa8baf4310ebf0271d2e272f922cb30287fbaa8f3b1203a4affd305d77bb89e` |
| 130 | posted | Base Sepolia | `0xbb896ad7cdbee00050e8e36361c8f05b908a4d406a4eee46cac89ef3f25c55e5` |
| 130 | evaluated | Lasna | `0x170f5e8ab33f257da28e36eded49ff013e4f3720817e9f08fcb0d6daabb985f3` |
| 130 | noTrade | Lasna | `0x170f5e8ab33f257da28e36eded49ff013e4f3720817e9f08fcb0d6daabb985f3` |
| 131 | opened | Lasna | `0x7d93f944838f28e99a4bddf8b4e07992346f37fcdc21f8449da99d56c04b3faa` |
| 131 | requested | Base Sepolia | `0x2e0c15b414974470304ccfc72f0efe2293aa55048c5812b7e78d0cd7cbbcba5a` |
| 131 | posted | Base Sepolia | `0x6fc24c81589ae7c3e910c84d8fb89b293be1bab14c273d38fac58a531118fd02` |
| 131 | evaluated | Lasna | `0x62d0846f5aff05e0081f4a74e9cfe82c74e99ae496cece4d8b98a050c30e8ade` |
| 131 | noTrade | Lasna | `0x62d0846f5aff05e0081f4a74e9cfe82c74e99ae496cece4d8b98a050c30e8ade` |
| 132 | opened | Lasna | `0x571b83932ffaf69f3587edd59a23e239d00383bf7791e1ef3e8a1a5d6d88932e` |
| 132 | requested | Base Sepolia | `0x951b76d0053a35d7eb28cb485740da2271654feac90ddc0e91c27d5f5cf88389` |
| 132 | posted | Base Sepolia | `0xe21af5a8f27a0b6b3716fb2e7788658d6ebe18cde64f4197306b371360927ba2` |
| 132 | evaluated | Lasna | `0x66fdb82b9185c0831f42a66611425f7493e5d932f3a8c7824d49b814698becbe` |
| 132 | noTrade | Lasna | `0x66fdb82b9185c0831f42a66611425f7493e5d932f3a8c7824d49b814698becbe` |
| 133 | opened | Lasna | `0x056dec326b55add1def1bf5995b9afa230d14ea36442971f8ab1cbe6b2edba70` |
| 133 | requested | Base Sepolia | `0x30dbd3e7f224ebe77a4479d5465f4f7284e41acadc03780e1e77d327106c0abe` |
| 133 | posted | Base Sepolia | `0x22c5c7205ee000ecd6604201d723cad11ae31bec17d4eb2eb9e29304c4328b9d` |
| 133 | evaluated | Lasna | `0x871c3877822a89461208c4a748b3cd78514867363837a59b06dfe66868e44ca8` |
| 133 | noTrade | Lasna | `0x871c3877822a89461208c4a748b3cd78514867363837a59b06dfe66868e44ca8` |
| 134 | opened | Lasna | `0xc2d52179130e34d0d398ad81b7e48a217158a17fa1b22eeae3f9b2cfcc35d8d8` |
| 134 | requested | Base Sepolia | `0x71c7ad2c448e951d0af702524526c4031c1625d72ece787991a20fc87bcf5b27` |
| 134 | posted | Base Sepolia | `0x8254a73d42e95637c295e11b5969d4daa13070924fa70a70fe79a481713d97d4` |
| 134 | evaluated | Lasna | `0x60b14d76036620d7857fde185f61949b1d0445f546e69537b6040567d338696a` |
| 134 | noTrade | Lasna | `0x60b14d76036620d7857fde185f61949b1d0445f546e69537b6040567d338696a` |
| 135 | opened | Lasna | `0x4923b7ddaa7fc299bf29ceb36597e2978817075ea2646126b1e7105a3ce990fa` |
| 135 | requested | Base Sepolia | `0x25aa52b90f59925b6517c85b90ccd3b043375567cac14a693be7caa54ba355ce` |
| 135 | posted | Base Sepolia | `0x26ecbcc043ab94b879c478b78df3ad96ab49f46a2fa13e51bc388df84880d9fe` |
| 135 | evaluated | Lasna | `0x29d19049182128af67b15bcd0e70531340926c8b644c9b8e2b6d928aad45e423` |
| 135 | noTrade | Lasna | `0x29d19049182128af67b15bcd0e70531340926c8b644c9b8e2b6d928aad45e423` |
| 136 | opened | Lasna | `0x1d8ffcabed98d4d54e7cb55da56ed83087ab2ba7ed2ab972f75a347cc2c13a15` |
| 136 | requested | Base Sepolia | `0xde0d43dddae853e339cb1aa400cb01a92d8adb7f918b500155229bed4643529c` |
| 136 | posted | Base Sepolia | `0x86bfe4c3cc4ff5b2d1800ead93caed6daa674821b46a38563d86005a9284336d` |
| 136 | evaluated | Lasna | `0x2af64cb6ef7eb5c850cebb6bc55145137cce136df947763d8879b642e58fdb70` |
| 136 | noTrade | Lasna | `0x2af64cb6ef7eb5c850cebb6bc55145137cce136df947763d8879b642e58fdb70` |
| 137 | opened | Lasna | `0x1d2ccae9494220092cfb26df40be95294f2d2949fea6caffe32e4ef9eea6018a` |
| 137 | requested | Base Sepolia | `0x8594a654acebc1bb484ded710bc79faf5dc62dbbeffc2fa4be6747ced073d6de` |
| 137 | posted | Base Sepolia | `0x751e27a137bf3b8b3c50b741db3563db235b86dda9554241d682dbbc6de761ff` |
| 137 | evaluated | Lasna | `0x083b6f74fde95718917ce81ba5d803164a91a78a0201d5b1f77bd6ffe886cd03` |
| 137 | noTrade | Lasna | `0x083b6f74fde95718917ce81ba5d803164a91a78a0201d5b1f77bd6ffe886cd03` |
| 138 | opened | Lasna | `0x1c0ea4e21468d50a18fed5c2d0fa24b198381c17c1a08faa00a1202b3f8b56e8` |
| 138 | requested | Base Sepolia | `0x020ecfbbf1e26ec60cd95376abade794e682a0990de08b4dc32b073538c414e5` |
| 138 | posted | Base Sepolia | `0x0c5d379a2ff69553e157d198824ff7f474d482c97659e909b734af4b00514f57` |
| 138 | evaluated | Lasna | `0x882e1cfc6a17c1d59acc9e3093182885d9839f9a995a4c2e526ded73cedf7e98` |
| 138 | noTrade | Lasna | `0x882e1cfc6a17c1d59acc9e3093182885d9839f9a995a4c2e526ded73cedf7e98` |
| 139 | opened | Lasna | `0x761261599ab062020ef498422301d8ade33533671b12b159efc354898ad1cc3c` |
| 139 | requested | Base Sepolia | `0x2f0fec8d71a3cf9f65ff9ea3d5d073b2b87167519d5ed9f8e998311d85887203` |
| 139 | posted | Base Sepolia | `0xa2bd46e7b56b3e9bb14840f29961ebd93db98652cb4de806652cab1dba538d01` |
| 139 | evaluated | Lasna | `0x0a2de3a6dbcb2194fb20a90e40bf2172e8bbd88b5a545211f32c932466ce27c1` |
| 139 | noTrade | Lasna | `0x0a2de3a6dbcb2194fb20a90e40bf2172e8bbd88b5a545211f32c932466ce27c1` |
| 140 | opened | Lasna | `0xbe7132ea17b878ac1ea5a637754761e14269944203f488215eea8abec984449a` |
| 140 | requested | Base Sepolia | `0x9dc010c9b0f087f52d53c19c9264926f3874b9d23d10882dbd00c4ff6bde1c87` |
| 140 | posted | Base Sepolia | `0x3c313cc78aedee895a028afdaa2d42d3c12ba18879365dab0ace0751c67dfa2a` |
| 140 | evaluated | Lasna | `0xae08c98177c140df4353fad0d90c7a31634183b4553de324ee907648a7c9b9cd` |
| 140 | noTrade | Lasna | `0xae08c98177c140df4353fad0d90c7a31634183b4553de324ee907648a7c9b9cd` |
| 141 | opened | Lasna | `0xc04c33bb33ff9cc3058018d1d90827170c85c789c9b2521180de197b6a40abb7` |
| 141 | requested | Base Sepolia | `0xa7a97ab514f9f75cd99fa56a50cd880b051c687ade81fae4508c8dac99427292` |
| 141 | posted | Base Sepolia | `0xd9a8581a92faac44cbc584bc4d0bc6599e9d99f9ec1d24c00ba11bea30e8acd2` |
| 141 | evaluated | Lasna | `0x586961e9e3220134a2f016d7a37bb2f380a9660804710f78ad11a273eebaaf87` |
| 141 | noTrade | Lasna | `0x586961e9e3220134a2f016d7a37bb2f380a9660804710f78ad11a273eebaaf87` |
| 142 | opened | Lasna | `0xca7bc12c74d2475d2130a7a1f9997cefaced7bb3994830068f635ec660bbffe1` |
| 142 | requested | Base Sepolia | `0x6bb053c4b721ba56de8972d975d8bedbc2cf339789b8ae47cbfbae7d84c95bd1` |
| 142 | posted | Base Sepolia | `0x04c782905e3c50a9cb677b2aacaf55fa547d9e746ebdce1304bf4c68ce5851c9` |
| 142 | evaluated | Lasna | `0x86bacf1f2da4fb5201b1cb358c50755bd0c2be829cfbc97f514603dd41938cd0` |
| 142 | noTrade | Lasna | `0x86bacf1f2da4fb5201b1cb358c50755bd0c2be829cfbc97f514603dd41938cd0` |
| 143 | opened | Lasna | `0xd1b6300fdd08a55f35e51ddf3e9109f5063c50493b52f0172b4c65733a41abd8` |
| 143 | requested | Base Sepolia | `0x5beb713df107e256966119e431922ae6d56ee2078836e0c74e98e85f5ce5c2ec` |
| 143 | posted | Base Sepolia | `0x0b5c34cf08436e926f3ac0901de34ae1e76f212cdde619c28f1b0a9c4738a6f4` |
| 143 | evaluated | Lasna | `0x42e0910578f1fd7cc94a3415ce7857641caaffabe970661ad3bcc5f64311fb5f` |
| 143 | noTrade | Lasna | `0x42e0910578f1fd7cc94a3415ce7857641caaffabe970661ad3bcc5f64311fb5f` |
| 144 | opened | Lasna | `0xc9e0d32e0a769eb8abc0a9c5d3bf219cfa304ff76930b279a77a6326630266f3` |
| 144 | requested | Base Sepolia | `0x2eb88f1acd1f4167d07828f8bdd83152c52e0d738d1a8913b8bd4b39394db732` |
| 144 | posted | Base Sepolia | `0x5756b7c214f8f59d8ec30bfc32298e908a0c9eb5805343bbf982791931d82f97` |
| 144 | evaluated | Lasna | `0x572f444b9f19db5a3f4923511e8aebd1e0991c68cdef4cd3415cd2496e2de4dd` |
| 144 | noTrade | Lasna | `0x572f444b9f19db5a3f4923511e8aebd1e0991c68cdef4cd3415cd2496e2de4dd` |
| 145 | opened | Lasna | `0x7222bbc2878888eab0de64c8b30c3b8e71bedfbd7e723149247496233204fbbf` |
| 145 | requested | Base Sepolia | `0x109a748bff30799e4ae30afed1d6cc0caf188eccea8b4b6390024d30f8f165d6` |
| 145 | posted | Base Sepolia | `0xdda687be7b57b9d1f25926d1e1385017cbcd538ecbb38e21c4f28d9edb01ef9c` |
| 145 | evaluated | Lasna | `0x6b99ed4989bcbb1dcdaef8b1f432a45384fd9321c4d727cf1ce47712a6c27f0f` |
| 145 | noTrade | Lasna | `0x6b99ed4989bcbb1dcdaef8b1f432a45384fd9321c4d727cf1ce47712a6c27f0f` |
| 146 | opened | Lasna | `0x7aae1ac50ca4bc881dc07cf13ef47404e9f4175f0a130e588c84b747d0e7a2c5` |
| 146 | requested | Base Sepolia | `0x732d3eff5ddec65043d87011ad2e160a3cf5f7c79043289a2f53d88e4d60aeb7` |
| 146 | posted | Base Sepolia | `0x612e625d15cdd4f0bd699c8daf786733f0f28d348e7129e26ec75b146f89399f` |
| 146 | evaluated | Lasna | `0xcd3f680cd4afe912776951cb48e9d8ee9527d06b995f63915637031dd8b0e515` |
| 146 | noTrade | Lasna | `0xcd3f680cd4afe912776951cb48e9d8ee9527d06b995f63915637031dd8b0e515` |
| 147 | opened | Lasna | `0xeab5daa48ee3c4ce11492b5379594fe6907cdf0fd8f87675e3112cedeeb0c0a8` |
| 147 | requested | Base Sepolia | `0xbd0971e23beddf31dc81e516e3341e7cdbabad9c9bfd3771ee7c0a508f6b1a4a` |
| 147 | posted | Base Sepolia | `0x31d91cd20b24c0da6efcbec5954f8ba6e7805c9b9f9d88efdafa4216bd3ac521` |
| 147 | evaluated | Lasna | `0x87088bc72133fdd1476c4714cc81502bcf460ca3d86c72f0f8a116951f97fe93` |
| 147 | noTrade | Lasna | `0x87088bc72133fdd1476c4714cc81502bcf460ca3d86c72f0f8a116951f97fe93` |
| 148 | opened | Lasna | `0xa60b40493db633e55159b64911241f6c098caccde0e40065c4e0d649cb297500` |
| 148 | requested | Base Sepolia | `0xf81da81abe3e894ae64540b8aebc6c373d469603abd4fdfa82a57acd92065c41` |
| 148 | posted | Base Sepolia | `0x24a27565c7d6a5c29f953ca652a322e7f401bcc4711e172791d55293ea1c0052` |
| 148 | evaluated | Lasna | `0x012898bcd33bc714006c46b9ef29d15360bfbbc1087275b4f8f23550875a4189` |
| 148 | noTrade | Lasna | `0x012898bcd33bc714006c46b9ef29d15360bfbbc1087275b4f8f23550875a4189` |
| 149 | opened | Lasna | `0x3c18e22462a6d25801c9bd4944ae4ee8e8171900c8d904913034dc44224cc909` |
| 149 | requested | Base Sepolia | `0xc854361444efaa8ec18c49166179e4f51b01e9214ad515777e5e54a93ee343bb` |
| 149 | posted | Base Sepolia | `0x1dfd0c195e4b4bcc943be282425e4b354097b7c0d0c28d6d995a1c93e3af8125` |
| 149 | evaluated | Lasna | `0x0f0aed968fe1dda76e53915925f58a1ddb9d5e8dff131cd440065a8e80147acf` |
| 149 | noTrade | Lasna | `0x0f0aed968fe1dda76e53915925f58a1ddb9d5e8dff131cd440065a8e80147acf` |
| 150 | opened | Lasna | `0x4b7e269b8ed28a4e3140a2183ff804bd763cf379052cb896d26a68fa76dc64e5` |
| 150 | requested | Base Sepolia | `0x37fbba6ba30760b607de1dbb366ae16cd6a77a62a2d509ff1a9ffe39dd8e3729` |
| 150 | posted | Base Sepolia | `0x1226ca589fbfb84a62fcd98b02137ed8afc9c57bd07ca95f2523a054298d215d` |
| 150 | evaluated | Lasna | `0xa1fc3e7b81a8a476dda91780b4a2c798e3aa0f23567a28ea4977b28fac53a2c0` |
| 150 | noTrade | Lasna | `0xa1fc3e7b81a8a476dda91780b4a2c798e3aa0f23567a28ea4977b28fac53a2c0` |
| 151 | opened | Lasna | `0xcc091430433b080cda9bb594ee85532dd96670902225416651b9f2d76cedacc4` |
| 151 | requested | Base Sepolia | `0x6e9972b47ad2260333d865a6ca7f84c0537b8e5d48abb2fc1b50182e001e1a2f` |
| 151 | posted | Base Sepolia | `0xfae91437956ca3c9b4c1f0facb599e85414deb2c33e2344e690fb6b343a5bb99` |
| 151 | evaluated | Lasna | `0xae15d527f551974e91b5939017fe4be2651af0f103e96cb7cbf39f205ff3bfeb` |
| 151 | noTrade | Lasna | `0xae15d527f551974e91b5939017fe4be2651af0f103e96cb7cbf39f205ff3bfeb` |
| 152 | opened | Lasna | `0x0e4abc3be066c3785907e843a159363d94b48787cb9cbe7ea0de95437c60351d` |
| 152 | requested | Base Sepolia | `0x2205cce430b7017204483d39a8532a893f9e52e3827cc78e815566b85a41fd55` |
| 152 | posted | Base Sepolia | `0x68556a39408325f22ca95435185e42b27abec25fd4b90089cc43d678bf7ec8b8` |
| 152 | evaluated | Lasna | `0x7a8278ea6ce204ae29f4fc31e7b6ecb438b94b1b990e98d80217242fd66a9864` |
| 152 | noTrade | Lasna | `0x7a8278ea6ce204ae29f4fc31e7b6ecb438b94b1b990e98d80217242fd66a9864` |
| 153 | opened | Lasna | `0xe602315c2e94606de59f4640ba28a0478a0347d29a9565bc8bc699029bce5099` |
| 153 | requested | Base Sepolia | `0x53badc065bc986c0d142d25c6bdfe8f6cdedb252661d6b14d97838aacd8884d0` |
| 153 | posted | Base Sepolia | `0x87a021770e6452eda252d7366f0cae500a2caf630b555b3768d375f5fcac38fb` |
| 153 | evaluated | Lasna | `0x63e32030da5e8b8d0088476bc57d24598206095c87f01a08791f1c9e6a085e2b` |
| 153 | noTrade | Lasna | `0x63e32030da5e8b8d0088476bc57d24598206095c87f01a08791f1c9e6a085e2b` |
| 154 | opened | Lasna | `0x8e212dbe823cf6d3e91441cff959143d7260979c1b15efa2b7a30abe840eead4` |
| 154 | requested | Base Sepolia | `0x1756157eb863ab70f159fba33390ddb4bc127b40a84c42dd3a34eb84d5accfe4` |
| 154 | posted | Base Sepolia | `0x112e013d2afd6dd9227db90e66bc65449f67bf3bfb5f45ce1282f0dc15823d07` |
| 154 | evaluated | Lasna | `0x81de87fe80451eb54209ba864da68d2bf4de01ef0be7323fa845251b9294b5f5` |
| 154 | noTrade | Lasna | `0x81de87fe80451eb54209ba864da68d2bf4de01ef0be7323fa845251b9294b5f5` |
| 155 | opened | Lasna | `0xe1e454473ac50e9f5cb89a6806f6d74eb49a347287f2234f0090ee43d56689fd` |
| 155 | requested | Base Sepolia | `0xf8c6dfb7e3924a2308bfb911385fc750323ecf9bfe1555b87d3d8dd15d32dfc0` |
| 155 | posted | Base Sepolia | `0x54f1c23c970aa32ded100e6815a4e4115594d29ad5e6585e58c5bdc37d3c50ae` |
| 155 | evaluated | Lasna | `0xf95db6c7dce4f21905ccce1a65aa8d04ab35ffce1912434af56d3575daa16628` |
| 155 | noTrade | Lasna | `0xf95db6c7dce4f21905ccce1a65aa8d04ab35ffce1912434af56d3575daa16628` |
| 156 | opened | Lasna | `0x0c98510a5dd7bc6e7cf223ac330675ee19effebc06b528e8cf9e897f5e5ce66e` |
| 156 | requested | Base Sepolia | `0x1d1bc0bdcf1a4f2a2b92c6a8cb49570049365b5162a5173d3758c52711aed9e0` |
| 156 | posted | Base Sepolia | `0x2e693281cb459d6b3a651d28036debfd2dde0762a0423bb25add33121342b9c2` |
| 156 | evaluated | Lasna | `0x0b27e3e5d7b5130d7a40552399ecc60a2c98ba7fc6cfab80828dce467cd26446` |
| 156 | noTrade | Lasna | `0x0b27e3e5d7b5130d7a40552399ecc60a2c98ba7fc6cfab80828dce467cd26446` |
| 157 | opened | Lasna | `0x6a8d7167c74ee2ab3c220f4d8407de9e2f03ac1a707c817f5ce881979d14e9c3` |
| 157 | requested | Base Sepolia | `0x3001ee63b390f3b9802fa734a5884926b415c20ba741ebea044c6ea889237199` |
| 157 | posted | Base Sepolia | `0x27c571b2afbbbf070448ae76192043b49c05220cbc3978305a306866f78c4894` |
| 157 | evaluated | Lasna | `0xa1aa44a1e7f30621b567369d2cece0977cb348bb64cc9c013c1d817899b2f197` |
| 157 | noTrade | Lasna | `0xa1aa44a1e7f30621b567369d2cece0977cb348bb64cc9c013c1d817899b2f197` |
| 158 | opened | Lasna | `0x87d950bb25e55c8e98b429aa540c362cb672df223bdc7e8452d444080daca5c4` |
| 158 | requested | Base Sepolia | `0x6d3fb133679fff0fdb0342c4f18618e62d35faf5a9f9f838a11e9cb32abd5d22` |
| 158 | posted | Base Sepolia | `0x6f000b51049a025269a43af1fc597d699d75f0388f9cf46c92b25cf890c56ac6` |
| 158 | evaluated | Lasna | `0xa5d6b2e4fb1bc1148201a999bf410d4c987f511058ba1197cda1e79ae5bdf07f` |
| 158 | noTrade | Lasna | `0xa5d6b2e4fb1bc1148201a999bf410d4c987f511058ba1197cda1e79ae5bdf07f` |
