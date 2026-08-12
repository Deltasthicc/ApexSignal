# Gate 7 holdout report

Generated 2026-08-12T12:29:36.631818+00:00. 20 clip(s), none used in Day-1 threshold tuning (see `human_labels.csv` for the excluded set).

**Every transcript below is raw ASR output, not manually verified.** Before using any of these as an actual demo clip, listen to it and correct the transcript by hand -- that step is not done here.

## Provenance (applies to every row below)

- ASR: `distil-whisper/distil-large-v3.5-ct2` @ `9793ccc07920e0f830e1dba0343efcdf0ef8c903`
- Tone encoder: `laion/voiceclap-commercial` @ `c291e8b13f3bd06e2c917d389133ffabccd53b70`
- Tone heads: `laion/voiceclap-commercial-attribute-heads` @ `8441fbd4050fb670c34453d99b3fdae7e8513667`
- Classifier: `MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33` @ `613e8c52c33e2bc0677ada4ad760f693e5e0f581`
- Arousal threshold: `2.565`, fatigue threshold: `1.1`, classifier null threshold: `0.5`

## Clips

| id | ASR transcript (unverified) | tone_label | tone_score | complaint_category |
|---|---|---|---|---|
| `2018_Abu_Dhabi_Grand_Prix_MAXVER01_33_20181125_173247` | Hey, can you tell me what was going on with the engine? So weird. There was unexpected PU protections, unexpected PU protections, Max. So those fails have disabled those sensors. So hopefully we don't have a recurrence of that. So apologies for that. We've done a good job getting back through the traffic. All right. Well, you overtook me. That's fine. You're ahead. He'll have to give that back. He'll give that back. | ToneLabel.CALM | 0.677 | None |
| `2018_Belgian_Grand_Prix_SEBVET01_5_20180826_155648` | and box, revised the box, push now. | ToneLabel.CALM | 0.603 | None |
| `2018_British_Grand_Prix_LEWHAM01_44_20180708_141943` | Gillis, you're doing a great job. Let's just keep battling up. Let's get in some points. I'm really sorry guys. Okay. No stress, Lewis, just head down. Let's get on with it, mate. Don't worry about it. The rear end is damaged. Yeah, we can still do something with it today, mate. | ToneLabel.ELEVATED_AROUSAL | 0.584 | None |
| `2018_Singapore_Grand_Prix_STOVAN01_2_20180916_200341` | Yes, I do. Can you check your drinks are working as well? Yeah, they are. | ToneLabel.CALM | 0.556 | None |
| `2018_United_States_Grand_Prix_KIMRAI01_7_20181021_144631` | Okay, we're better for shopping to move like it. | ToneLabel.CALM | 0.538 | None |
| `2018_United_States_Grand_Prix_SEBVET01_5_20181021_134937` | Keep it up in 42, 3, and best up in 40.9. Keep your head down, the important phase. | ToneLabel.ELEVATED_AROUSAL | 0.561 | None |
| `2019_Abu_Dhabi_Grand_Prix_SEBVET01_5_20191201_145445` | And thank you for the season. Okay, thanks to you. Thank you, thank you to all the mechanics, great work, thank you to all the mechanics. You are Ferrari, thank you. | ToneLabel.CALM | 0.614 | None |
| `2019_Bahrain_Grand_Prix_KIMRAI01_7_20190331_170813` | How is the front wing? You can drop one step. | ToneLabel.ELEVATED_AROUSAL | 0.571 | None |
| `2019_German_Grand_Prix_SEBVET01_5_20190728_151032` | and try to stay close as possible to Kemi, it should close the pack. | ToneLabel.CALM | 0.816 | None |
| `2020_Bahrain_Grand_Prix_ESTOCO01_31_20201129_153648` | What is Norris doing? Guys, can you hear me? Yes, go ahead. What position am I in? Because Norris just passed me. You are P8, Norris is P7, Daniel is P6. So as I said, on the grid you'll have Daniel right in front of you and Norris to your right ahead of you. | ToneLabel.CALM | 0.624 | None |
| `2020_British_Grand_Prix_GEORUS01_63_20200802_133836` | What do you think it's going on at a turn four? I had a couple of lockups there. More than normal. The balance actually felt a bit more consistent through three and four versus quality. George, I think that a wind strength has dropped quite a bit. I'll check on a wind map. Copy. You sound pretty loud by the way James on that headset. | ToneLabel.CALM | 0.758 | None |
| `2021_Austrian_Grand_Prix_MAXVER01_33_20210704_151605` | Can I go for faster lap? What mode? Okay, let's have mode two. Mode two. You still currently have purple lap. Mode two for one lap. But don't totally abuse the tires, please. | ToneLabel.ELEVATED_AROUSAL | 0.528 | None |
| `2021_Belgian_Grand_Prix_LANSTR01_18_20210829_142809` | Yeah, I can't see anything behind the car in front of me. There's some acroplaning on the back straight. | ToneLabel.CALM | 0.553 | None |
| `2021_French_Grand_Prix_ESTOCO01_31_20210620_144338` | Okay, some of the hard runners that stopped behind you are now going slower, so pace is okay at the moment. | ToneLabel.FATIGUED | 0.723 | None |
| `2021_Portuguese_Grand_Prix_LEWHAM01_44_20210502_153455` | That is a pretty shot. | ToneLabel.ELEVATED_AROUSAL | 0.549 | None |
| `2021_Saudi_Arabian_Grand_Prix_MAXVER01_33_20211205_181737` | Mate, Louis is sleeping way more than 10 cars, and she's not okay. | ToneLabel.ELEVATED_AROUSAL | 0.502 | None |
| `2023_Australian_Grand_Prix_LEWHAM01_44_20230402_071058` | So, Gabton Alonso 1.2. Because this can't be on the same strategy as us, man. If they were to stop again, Lewis, we'd think they would struggle with the tyres they have available. | ToneLabel.CALM | 0.536 | None |
| `2023_Austrian_Grand_Prix_CARSAI01_55_20230702_145458` | Let's extend to see if we got your safety car. | ToneLabel.ELEVATED_AROUSAL | 0.600 | None |
| `2023_Qatar_Grand_Prix_LOGSAR01_2_20231008_190710` | I don't feel well, man. Joe, are you retiring, mate? Are you retiring? It's your call, buddy. You're the one making the call if you want to retire or not, Logan. There's no shame to retire if you're feeling unwell. I need a stop. | ToneLabel.ELEVATED_AROUSAL | 0.614 | None |
| `2024_Mexico_City_Grand_Prix_LANSTR01_18_20241027_151856` | Remember you can use early energy into one into 40 | ToneLabel.CALM | 0.792 | None |