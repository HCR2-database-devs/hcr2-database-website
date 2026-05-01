--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.10
-- Dumped by pg_dump version 9.6.10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: _map; Type: TABLE; Schema: public; Owner: rebasedata
--

CREATE TABLE public._map (
    "idMap" smallint,
    "nameMap" character varying(19) DEFAULT NULL::character varying,
    special smallint
);


ALTER TABLE public._map OWNER TO rebasedata;

--
-- Name: _news; Type: TABLE; Schema: public; Owner: rebasedata
--

CREATE TABLE public._news (
    id smallint,
    title character varying(50) DEFAULT NULL::character varying,
    content character varying(1559) DEFAULT NULL::character varying,
    author character varying(14) DEFAULT NULL::character varying,
    created_at character varying(1) DEFAULT NULL::character varying
);


ALTER TABLE public._news OWNER TO rebasedata;

--
-- Name: _pendingsubmission; Type: TABLE; Schema: public; Owner: rebasedata
--

CREATE TABLE public._pendingsubmission (
    id smallint,
    "idMap" smallint,
    "idVehicle" smallint,
    distance integer,
    "playerName" character varying(70) DEFAULT NULL::character varying,
    "playerCountry" character varying(82) DEFAULT NULL::character varying,
    "submitterIp" character varying(39) DEFAULT NULL::character varying,
    status character varying(8) DEFAULT NULL::character varying,
    submitted_at character varying(1) DEFAULT NULL::character varying,
    "tuningParts" character varying(57) DEFAULT NULL::character varying
);


ALTER TABLE public._pendingsubmission OWNER TO rebasedata;

--
-- Name: _player; Type: TABLE; Schema: public; Owner: rebasedata
--

CREATE TABLE public._player (
    "idPlayer" smallint,
    "namePlayer" character varying(15) DEFAULT NULL::character varying,
    country character varying(32) DEFAULT NULL::character varying
);


ALTER TABLE public._player OWNER TO rebasedata;

--
-- Name: _sqlite_sequence; Type: TABLE; Schema: public; Owner: rebasedata
--

CREATE TABLE public._sqlite_sequence (
    name character varying(17) DEFAULT NULL::character varying,
    seq smallint
);


ALTER TABLE public._sqlite_sequence OWNER TO rebasedata;

--
-- Name: _tuningpart; Type: TABLE; Schema: public; Owner: rebasedata
--

CREATE TABLE public._tuningpart (
    "idTuningPart" smallint,
    "nameTuningPart" character varying(17) DEFAULT NULL::character varying
);


ALTER TABLE public._tuningpart OWNER TO rebasedata;

--
-- Name: _tuningsetup; Type: TABLE; Schema: public; Owner: rebasedata
--

CREATE TABLE public._tuningsetup (
    "idTuningSetup" smallint
);


ALTER TABLE public._tuningsetup OWNER TO rebasedata;

--
-- Name: _tuningsetupparts; Type: TABLE; Schema: public; Owner: rebasedata
--

CREATE TABLE public._tuningsetupparts (
    "idTuningSetup" smallint,
    "idTuningPart" smallint
);


ALTER TABLE public._tuningsetupparts OWNER TO rebasedata;

--
-- Name: _vehicle; Type: TABLE; Schema: public; Owner: rebasedata
--

CREATE TABLE public._vehicle (
    "idVehicle" smallint,
    "nameVehicle" character varying(16) DEFAULT NULL::character varying
);


ALTER TABLE public._vehicle OWNER TO rebasedata;

--
-- Name: _worldrecord; Type: TABLE; Schema: public; Owner: rebasedata
--

CREATE TABLE public._worldrecord (
    "idMap" smallint,
    "idVehicle" smallint,
    "idPlayer" smallint,
    distance integer,
    current smallint,
    "idTuningSetup" character varying(3) DEFAULT NULL::character varying,
    questionable smallint,
    questionable_reason character varying(42) DEFAULT NULL::character varying
);


ALTER TABLE public._worldrecord OWNER TO rebasedata;

--
-- Data for Name: _map; Type: TABLE DATA; Schema: public; Owner: rebasedata
--

COPY public._map ("idMap", "nameMap", special) FROM stdin;
1	Countryside	0
2	Forest	0
3	City	0
4	Mountain	0
5	Rustbucket Reef	0
6	Winter	0
7	Mines	0
8	Desert Valley	0
9	Beach	0
10	Backwater Bog	0
11	Racer Glacier	0
12	Patchwork Plant	0
13	Switchback Savannah	0
14	Gloomvale	0
15	Overspill Fun Rig	0
16	Canyon Arena	0
17	Cuptown	0
18	Sky Rock Outpost	0
19	Forest Trials	1
20	Intense City	1
21	Raging Winter	1
22	Spring Falls	0
\.


--
-- Data for Name: _news; Type: TABLE DATA; Schema: public; Owner: rebasedata
--

COPY public._news (id, title, content, author, created_at) FROM stdin;
1	This is test!	I hope you like our cool website!!!!	nipatsuyt#0	
2	This is test! #2	Testing. :)	nipatsuyt#0	
3	Test #3	Happy new year 2026	titaniumhcr2#0	
4	Changelog for todays update	- Updated footer with fixed copyright stuff\n- Removed Hcr2 logo and donation button\n- Changed website name to "HCR2 Adventure Records (unofficial)"\nNew records will be added during next weekend.\nOur website also reached over 3000 visits during first 24 hours. Thank you very much!	nipatsuyt	
5	Bot attack	Yesterday we experienced an unusual wave of automated bot traffic that caused increased load on some parts of our website. We have identified the source of this activity and confirmed that it originated from external automated virtual machine environments. No user data was accessed or compromised, and no changes were made to site content. Additional backend security measures and traffic filtering rules have now been deployed, and we will continue strengthening our backend security to better protect the website against similar activity in the future. As part of these changes, record submissions are temporarily disabled while we complete further backend security improvements. All other services are operating normally. Thank you for your patience, and sorry for any inconvenience this may have caused.\n- Nipatsu & Titanium	nipatsuyt	
6	Changelog for today's update	- Added captcha in submit form and increased backend security\n- New custom-made logo\n- New UI\n- You can now filter records with multiple vehicles / maps simultaneously\n- Filter with distance\n- Added country flags\n- Formatted distance integers (123 456 789) for easier reading\n- More stats	titaniumhcr2	
7	It's over...	After a lengthy reign, it appears that ð©ðª Zorro has finally been dethroned. For years, this exceptionally talented player tirelessly worked to hold the title for the most Adventure Mode World Records. However, today, he has been surpassed by ðµð± Kacp, who now boasts 58 World Records ; one more than Zorro. Congratulation	titaniumhcr2	
8	Website status update!	We want to be transparent about the current situation with the website. Right now, the site is not working as it should. While records and stats are still showing normally, some important parts of the site are having problems. Recent changes we’ve made are not being applied correctly, and the admin panel is not functioning the way it should. On top of that, there are some internal errors that are causing the site to be much slower than usual. We’ve spent time investigating this and, at this point, we believe the best next step is to move the website to a different hosting provider to see if that resolves these issues. Unfortunately, this isn’t something we can fix instantly, and it requires some backend changes.\n\n⚠️ Because of this, there may be temporary downtime during the host migration. We’ll do our best to keep it as short as possible and minimize disruption.\n\nThanks a lot for your patience and understanding while we work on fixing this properly. We’ll post another update as soon as things are stable again.\n\nNipatsu & Titanium	nipatsuyt	
9	Rest in Peace	All of ð¨ð¿ Peace's World Records (5 in total) have been removed from the database due to this player being involved in a cheating scandal (VIP sharing, getting dozens of stars using illegitimate methods, and god knows what else).\n\nAfter being exposed for their actions, Peace was forced to delete their account, subsequently removing all of his possibly hacked records from the leaderb	titaniumhcr2	
10	Glider Masteries	Glider Masteries are now officially out ! Prepare your propellers and your indestructible wings, and go get some new World Records with the now-even-more-broken-somehow Glider ð	titaniumhcr2	
11	1,500,000 m	Glider has just passed 1.5 million meters of total distance ! Crazy !	titaniumhcr2	
12	New update - Tuning Parts	The newest update is now online, including... TUNING PARTS ð\nEverything should now be available on the site.\n\nOn mobile, the update usually works after clearing the website cache or refreshing a few times. However, in some cases removing the cache doesn’t help, and the old version may still show. We’re aware of this and are also investigating what’s causing it.\n\nOn PC, things aren’t working as expected yet. Records and stats load normally, but some of the new features may be missing. We’re currently investigating this issue as well and working on a fix.\n\nYou can also now share links to individual records! (https://www.hcr2.xyz/?view=records&recordId=287&map=Beach) \nThere’s a share button next to each record, so you can easily send a direct link to a specific run.\nIf you find any bugs or notice anything weird, please let us kn	titaniumhcr2	
13	A New Admin has been appeared! ð	Hello y'all, im Bir insan, if you active on the hcr2 discord servers (mainly on AL), following the Titanium etc. you probably know me as the Kebab guy, Blush(ð) guy or else. Im happy to announce that im the new admin for the website from now on, Since both Titanium and Nipatsu are working on improve the website, they can't really add the new records frequently, so im here for that ð. Thank you for the Titanium and Nipatsu to pick me as the new Admin, it's a honor for me ð.\n\nIf you guys want to say anything related to the world records, you can DM me through discord, my DMs are always open and i will respond back asap ð.\n\nThank you  for the Titanium and Nipatsu again for giving me this role. \n\nHave a	birinsan	
14	A new milestone for Intense City! ð	With the recent 5km with Snowmobile by ð·ðº Mushroom, Intense City now has 20 5kms in to	birinsan	
15	Bolt Masteries	Bolt Masteries are now officially out ! Is Bolt about to become the top-tier adventure vehicle that it was always destined to be ? Prove it by getting some new World Records with the supreme Bolt ! ð	titaniumhcr2	
16	Bluestar	The 2 Glider records from ð·ðº Bluestar were removed due to the Bluestar account being an alt account of a blacklisted player (ð§ð·	titaniumhcr2	
32	Monthly recap : March 2026	- New special map 5ks : Motocross in Intense City, Stocker in Forest Trials \n\n- New 10ks : Stocker in every regular map \n\n- New 100,000 m distances : Stocker in Desert Valley, Glider in Mines\n\n- Other noteworthy records : \n\nGlider in Mines 100,020 m by ð¬ð§ Patbrick. An impressive new 6-digit distance that frankly came out of nowhere. This was the first 100km in Mines ! Ironic that a plane-like vehicle achieved this in a cave map.\n\nGlider in Cuptown 14,966 m by ðºð² ð«ð The first pass of the obstacle at 11.2km for a vehicle other than Motocross was achieved by ATV, but very soon later, Glider managed to push the record even further, getting the All-Vehicle World Record in the process.\n\nStocker in Beach 95,791 m by ð«ð® Nikis. This impressive record goes to show how much potential the newest 	titaniumhcr2	
17	Ahout TAS practice	On this website, we are committed to ensuring the legitimacy of the records stored in the database.\n\nSome players, such as ðºð² Crash77, are known to use the TAS (Tool-Assisted Speedrun) technique to practice certain difficult parts of adventure maps, repeating the part several times from a save point located at the last fuel (instead of starting over from the beginning as in a normal game).\n\nThey then use the skills and knowledge of the map acquired through TAS to play this combination and achieve the world record legitimately. While the record itself is legitimate, the method used to achieve it is ethically questionable.\n\nThis advanced training method used by TAS players puts regular players at a significant disadvantage. A legitimate player would likely need several days of practice to achieve a particularly difficult 10,000m record, while someone who has trained with TAS can easily achieve the same record in less than 10 attempts.\n\nIn addition, TAS imposes hardware requirements that many regular players cannot meet, such as a PC and storage space for each save file. \n\nThat's why we've decided to add a new records section called “Questionable Records”, where records in this category will be moved, along with other records whose legitimacy we are unsure of.\n\nYou will soon be able to decide whether or not to display these “Questionable Records” in the records table and on the statistics page by enabling or disabling the “Show questionable records” option in the menu, depending on whether you feel like these records should be inc	titaniumhcr2	
18	Monthly recap : February 2026 ⭐️	- New special map 5ks : Snowmobile & Bolt in Intense City, Formula & Rotator in Forest Trials\n- New 100,000 m distance : Bolt in Desert Valley \n\n- Other noteworthy records : \n\nFormula in Forest Trials 5,082 m by ð¬ð§ Billy 900. Billy spent 65 h and 38 minutes grinding this extreme combo, which ultimately led to his very first World Record. Absolutely deserved.\n\nSuperbike in Spring Falls 11,113 m by ð«ð® Nakkibiilo. Already a very difficult 10km, but this Finnish underdog was the first one to collect the first fuel after 10km.\n\nGlider in City 70,477 m by ð¨ð³ Regotn. This combo received quite a few improvements this month, and eventually, this Chinese player was the first one to cross 70 km, asserting Glider's 	titaniumhcr2	
19	WHAT THE F*CK	Well that came out of nowhere ð The first 100km in Mines has just been reached by ð¬ð§ Patbrick with Glider ! Amazing !\n\nGlider now has 5 six-digit distances, which is as many as CC-EV has r	titaniumhcr2	
20	Erratum	Formula in Forest Trials is not a new 5,000 m as stated in the February 2026 monthly recap, as a distance superior to 5,000 m had already been set prior to that month. My apologies for the oversight.	titaniumhcr2	
21	New updates!	We’ve just updated the Records section with some key improvements:\n\nCleaner Filters:\n- The Records tab filters have been reworked—faster, easier, and more intuitive for browsing maps, vehicles, tuning parts, and players.\n\nQuestionable Records:\n- A new “Questionable” tag marks runs that might be TAS-trained or otherwise uncertain. These aren’t automatically invalid—they’re just flagged for transparency. You can filter to see only Questionable records if you like.\n\nBug Fixes:\n- Minor bugs and inconsistencies have been fixed to improve stability and usability.	nipatsuyt	
22	About TAS practice (2)	According to the results of my latest YouTube poll, a VAST majority of people don't mind if a player uses Tool-Assisted-Speedrun / savestates to practice a specific combo before getting the World Record on this combo in a legit run. \n\nAs a result of this democratic poll, records which are TAS-practiced will be removed from the Questionable Records section, and accepted as verified records.\n\nThe Questionable Records section will still remain for records from players who we aren't sure are legitimate, but TAS-trained records will no longer be part of this category as they are mostly accepted by the community.	titaniumhcr2	
23	ATV Masteries	ATV Masteries are now officially out ! Certainly not powerful enough to pull a girlfriend, but definitely capable of turning ATV into an Adventure staple.	titaniumhcr2	
24	The Zorro falloff is crazy	Zorro has now fallen to 3rd place in the World Records by player leaderboard, as ð³ð¿ Ndwg just got his 50th current World Record. Will we see a Zorro comeback ? Probably	titaniumhcr2	
25	It's over for Motocross...	ð©ðª FelixCraft has just achieved a distance of 12,294 m in Cuptown with ATV, defeating Motocross and securing the car's first All-Vehicle world record since its debut. Cong	titaniumhcr2	
26	Glider rules once again. ð	After ATV achieved All-Vehicle world in Cuptown,  ðºð¸ð«ð achieved a distance of 12,681 with Glider in Cuptown!\n\nGlider is once again showing itself as the best vehicle in 	birinsan	
27	ATV auto-clicker glitch	A new glitch with ATV has been discovered, in which ATV's hook is continuously activated and deactivated, so fast that it actually gives you a constant boost forward, without even hooking onto anything. This is very powerful, as it allows ATV to literally fly over the entire cave section in Far Far Away (which only Pre-Nerf Minibus managed to do prior to that).\n\nUnlike Motocross Mid-Air Jump Shocks, or the now defunct Moonlander Eco Thrust, this is extremely unfair, as players with auto-clickers can abuse this glitch to get way faster times or longer distances, and should absolutely be patched out of the game.\n\nRecords using this glitch WILL NOT be included here.	titaniumhcr2	
28	Lucas on topð	ð«ð· Lucas beat a whopping 14 WORLD RECORDS in the past 3 days, which allowed him to pass Zorro, Kacp and Ndwg, and become the player with the most World Records in Adventure ! Crazy s	titaniumhcr2	
29	Edit : it's 16 WRs not 14	.	titaniumhcr2	
30	A New Vehicle, The Stocker, is joining the roster!	A Nascar inspired Muscle car rip-off vehicle that has a boost similar to CCEV but activated by a button just like glider's propeller boost...\n\nCan this vehicle can become a top vehicle among the other top adventure vehicles or even defeat them? We will find out very soon!	birinsan	
31	Stocker	Stocker is now available from the shop, which means non-Pitcrew Stocker records from the leaderboards will be added here in addition to the many challenge runs already added. \nAdditionally, Stocker has received a slight nerf in v1.72.1, but due to this nerf happening very early on, before most of the playerbase had chance to try the vehicle, we consider that pre-nerf records are easily beatable post-nerf, and therefore will keep pre-nerf records on this database.	titaniumhcr2	
33	Additions to the hcr2.xyz Staff	We are happy to announce the appointment of two new administrators for the hcr2.xyz website !\n\n- DanioDuck (Netherlands): As one of the top 10 Hill Climb Racing 2 players in terms of current World Records, he has extensive knowledge of the game's competitive scene and will assist in guaranteeing that the World Records in the database are accurate and legitimate.\n- Noya (France): A seasoned developer with prior experience working on HCR2-related projects, who is also an enthusiastic Hill Climb Racing 2 player. He will share his knowledge and expertise to enhance the website both technically and aesthetically.\n\nStay tuned for future improvements to the website ! ð	titaniumhcr2	
\.


--
-- Data for Name: _pendingsubmission; Type: TABLE DATA; Schema: public; Owner: rebasedata
--

COPY public._pendingsubmission (id, "idMap", "idVehicle", distance, "playerName", "playerCountry", "submitterIp", status, submitted_at, "tuningParts") FROM stdin;
1	1	1	1000	Nipatsu		127.0.0.1	rejected		
2	1	1	1000	Nipatsu		127.0.0.1	rejected		
3	1	2	1000	Nipatsu1		127.0.0.1	rejected		
4	2	3	1000	Nipa	Finland	127.0.0.1	rejected		
5	5	11	1230	jgkih	Estonia	127.0.0.1	rejected		
6	1	15	676767	Noobmaster69	Ohio	::1	rejected		
7	3	15	67	Noobmaster69	Ohio	::1	rejected		
8	20	33	5067	DanioDuck		::1	approved		
9	13	5	10	Nipatsu		127.0.0.1	rejected		
10	21	14	3791	Peace	Czechia	2804:1b3:704e:c3aa:c9f4:31fa:d7ef:63d8	approved		
11	16	30	6439	Peace	Czechia	2804:1b3:704e:c3aa:c9f4:31fa:d7ef:63d8	approved		
12	5	30	11283	Ndwg	New Zealand	2804:1b3:704e:c3aa:c9f4:31fa:d7ef:63d8	approved		
13	3	33	23804	Joplin	USA	2804:1b3:704e:c3aa:c9f4:31fa:d7ef:63d8	approved		
14	8	33	39373	Kacp	Poland	2804:1b3:704e:c3aa:c9f4:31fa:d7ef:63d8	approved		
15	14	30	8034	NDWG		159.146.20.120	rejected		
16	1	14	20522	Hill Driver	Turkiye	159.146.20.120	rejected		
17	15	14	30331	Lucas	France	2a01:cb1c:59f:a600:9152:7c4c:b351:ff24	approved		
18	1	1	67676767	BerndVM1	PS	185.185.50.64	rejected		
19	1	1	67676767	BerndVM1	PS	185.185.50.64	rejected		
20	1	1	67676767	BerndVM1	PS	185.185.50.64	rejected		
21	1	1	67676767	BerndVM1	PS	185.185.50.64	rejected		
22	1	1	67676767	BerndVM1	PS	185.185.50.64	rejected		
23	18	27	86743	4 Can Tapanç		146.70.137.243	rejected		
24	13	16	15369	IceDragonVN	Việt Nam	116.98.249.197	rejected		
25	5	30	11283	Ndwg	Australia (I think ð	2a01:cb16:201b:2b43:0:5d:2bf3:4a01	rejected		
26	5	30	11283	Ndwg	New Zealand	2407:7000:b018:4100::1002	rejected		
27	5	8	6762	asdfghjkl		77.239.166.121	rejected		
28	21	31	3832	Leandertaler	Germany	80.208.211.53	rejected		
29	8	31	27900	Leandertaler	Germany	80.208.211.53	rejected		
30	20	31	4721	ZombiX	Poland	140.213.202.207	approved		
31	14	14	11707	Lucas64	France	2001:861:8050:5ba0:a1ac:4f90:6b90:64ee	approved		
32	2	26	8842	ZorritoPRO	México	2806:2f0:3181:f937:5b51:b738:718a:f14a	rejected		
33	19	27	13503	ndwg	Australia	2a00:1858:1054:8aee:7153:bd4e:4be4:2740	rejected		
34	19	33	5794	Toast	Australia	2a00:1858:1054:8aee:7153:bd4e:4be4:2740	approved		
35	19	20	5949	Nasa PC	Usa	2a00:1858:1054:8aee:7153:bd4e:4be4:2740	rejected		
36	2	33	40237	AT36~SA	South Africa	102.249.37.13	rejected		
37	20	27	1915	Lucifer	Australia	124.158.98.22	rejected		
38	2	24	62343	ð	USA	108.18.217.72	rejected		
39	14	32	11093	Zoobaman	Canada	2604:3d09:7581:e000:44a5:24fe:8ed0:a863	approved		
40	19	12	2392	PALMTREE|SM	USA	2600:1005:a027:1dbd:6867:fe91:c6fc:7463	rejected		
41	21	16	957	PALMTREE|SM	USA	2600:1005:a027:1dbd:6867:fe91:c6fc:7463	rejected		
42	1	1	67676767	WARNING	FR	88.253.210.221	rejected		
43	1	1	67676767	WARNING	FR	88.253.210.221	rejected		
44	1	1	67676767	WARNING	FR	88.253.210.221	rejected		
45	1	1	67676767	WARNING	FR	88.253.210.221	rejected		
46	1	1	67676767	WARNING	FR	88.253.210.221	rejected		
47	6	2	23755	Lite	Russia	5.228.81.40	rejected		
48	8	2	67352	Lite	Russia	5.228.81.40	rejected		
49	17	2	10744	Lite	Russia	5.228.81.40	rejected		
50	1	1	676767	BERNDVM1	PS	185.213.193.123	rejected		
51	17	2	10744	Lite	Russia	5.228.81.40	rejected		
52	8	2	67352	Lite	Russia	5.228.81.40	rejected		
53	6	2	23755	Lite	Russia	5.228.81.40	rejected		
54	6	2	23755	Lite	Russia	5.228.81.40	rejected		
55	17	33	10764	Ndwg	New Zealand	49.226.207.141	approved		
56	8	26	431957	ezWRguy	Albania	31.5.17.97	rejected		
57	9	33	47153	Me off-road	Brasil	2804:18:10fa:5cf1:1889:58c:363c:ee88	rejected		
58	21	19	520	Great Reaper	USA	2600:4040:bfee:4f00:b92c:980:3b13:4b22	rejected		
59	8	5	10000	[♕‿✪]		92.48.43.20	rejected		
60	21	18	0	sigma67		2a10:a5c0:184:7f00:aca2:5a8e:a6ac:d9e1	rejected		
61	8	27	10124	addudefaluter	India	2405:201:4003:e11c:d99b:27d5:6fc1:8ca3	rejected		
62	4	13	1	VOID		108.192.70.178	rejected		
63	2	23	24919	VICTOR™ 2026	Brazil	2804:14d:8e8d:880a:4836:6001:46e3:1ad2	rejected		
64	1	10	16057	drained.	Brazil	179.178.249.105	rejected		
65	2	20	29087	[JDM]Stygo	Deutschland	2a00:fbc:e391:9638:5c2d:400d:a683:372a	rejected		
66	4	12	19126	RL|UWEð		78.42.242.103	rejected		
67	16	13	13534	AnonimChik	Russia	169.150.209.163	rejected		
68	7	7	6275	ForMyCat		66.9.166.158	rejected		
69	1	21	9179	Nate_Hıggªs	Antartica	146.241.202.95	rejected		
70	9	33	12	Little Timmy	Romania	86.123.229.172	rejected		
71	5	18	13892	Cool guy	Germany	90.186.69.59	rejected		
72	9	5	66929	Joplin		103.216.221.102	rejected		
73	20	19	396	GoombaPro:3		2603:6081:6f0:7390:7828:c727:f3d5:1865	rejected		
74	8	30	10763	Guigofx_07	Brazil	2a09:bac1:1100:a098::61:2a7	rejected		
75	22	24	12456	ð	USA	108.18.217.72	rejected		
76	2	20	6906	Iampro12468		173.211.245.98	rejected		
77	11	29	11121	Ndwg	New Zealand	2407:7000:b018:4100::1004	approved		
78	3	20	21058	FL|PrØtèCT	USA	103.10.21.39	rejected		
79	4	30	4833	LUNAR JANET	Germany	2402:3a80:42a8:57c8:23d7:56aa:17fd:4a9a	rejected		
80	20	24	4965	Mushroom	Russia	2a00:1858:1054:8aee:489c:6c31:3dc5:bdf9	approved		
81	20	20	15000	@Luke	Germany	91.137.127.12	rejected		
82	21	9	4055	Kacp	Poland	2a00:1858:1054:8aee:3660:28e:bd12:20ad	approved		
83	20	24	5050	Mushroom	Russia	2a00:1858:1054:8aee:3660:28e:bd12:20ad	approved		
84	22	27	15762	ð	USA	108.18.217.72	rejected		
85	7	33	7056	[PR]Bubby	USA	2600:382:1078:425d:e0c4:e038:4670:9e80	rejected		
86	9	23	19456	[LTS] bullet	Australia	203.123.66.216	rejected		
87	1	14	20542	Hill Driver	Turkiye	2a00:1858:1054:8aee:c51f:8c24:685c:32b9	approved		
88	2	26	10237	Rk925thepro	United States	2607:fb90:b394:50d4:45c9:72f1:ac0b:9a71	rejected		
89	8	12	7657	Rk925thepro	United States	2607:fb90:b394:50d4:45c9:72f1:ac0b:9a71	rejected		
90	7	20	6141	Rk925thepro	United States	2607:fb90:b394:50d4:45c9:72f1:ac0b:9a71	rejected		
91	1	20	8629	Rk925thepro	United States	2607:fb90:b394:50d4:45c9:72f1:ac0b:9a71	rejected		
92	13	33	15683	Toast	Australia	2407:7000:b018:4100::1002	approved		
93	9	33	52271	AUSTRAL	France	2a02:8428:af44:4401:d137:77f0:c552:6270	approved		
94	6	27	79201	drained	ð	2804:14d:5c80:9903:c9f4:31fa:d7ef:63d8	rejected		
95	14	29	10501	Ndwg	New Zealand	2407:7000:af94:ab00:a4b4:84cb:279b:eb93	rejected		
96	2	27	11750	never be al9	India	2403:a080:410:6be8:a54a:451:fd90:9f39	rejected		
97	9	20	95789	AUSTRAL		2a04:cec0:1220:e217:2de7:7879:5ea2:3679	approved		
98	9	14	44000	AK|~$uM!t~	India	223.188.72.229	rejected		
99	20	15	10069	Noodmaster69	Tajikistan	83.85.206.91	rejected		
100	2	12	11065	ezwrguy313		31.5.17.97	rejected		
101	11	17	11006	Kacp	Poland	95.49.56.221	approved		
102	7	33	24139	TORTU	Canada	161.29.21.175	approved		
103	11	17	11119	Ndwg	ð³ð¿ New Z	118.93.235.177	approved		
104	16	13	13534	Airinetto (kacp got this after me, and this is my new nickname)	Russia	84.17.46.88	rejected		
105	20	15	6767	Noobmaster67	France	83.85.206.91	rejected		
106	7	5	1	e	e	2a02:8429:198:f901:c07b:b2b0:fedf:e16c	rejected		
107	6	31	21171	Ralph	Philippines	136.158.120.146	rejected		
108	11	8	23113	Ndwg	New Zealand	193.50.193.25	approved		
109	13	17	15688	Toast	Australia	118.93.235.177	approved		
110	9	14	67156	AUSTRAL	France	2a04:cec0:1227:1353:b484:24af:ce74:69d0	approved		
111	8	5	87950	Lucas	France	159.146.8.171	rejected		
112	14	8	11895	Ndwg	New Zealand	2407:7000:b018:4100::1006	rejected		
113	22	31	12218	Zandrik	Russia	193.50.193.25	approved		
114	9	20	8126	Rk925thepro	United States	64.79.55.117	rejected		
115	13	10	15943	toast.	Australia	119.18.0.189	rejected		
116	5	33	20696	SI| Advantoer	United States	74.215.67.238	rejected		
117	6	33	26050	Advantoer	United States	74.215.67.238	rejected		
118	22	6	13281	ð	USA	108.18.217.72	rejected		
119	9	28	21971	AUSTRAL		2a04:cec0:1205:c6a7:a5c3:1553:a53b:dd41	approved		
120	1	1	6000	CO²	Germany	50.104.182.190	rejected		
121	11	28	8819	Can Tapanc	Turkiye	159.146.9.239	approved		
122	13	28	11799	Toast	Australia	49.225.116.78	approved		
123	2	19	11080	PG|誰か…		202.5.100.72	rejected		
124	9	1	69826	Yanix		2a02:8428:af44:4401:c02b:c2b8:e840:fcd4	rejected		
125	13	15	15543	Toast	Australia	2407:7000:b018:4100::1007	approved		
126	4	23	16674	AlonePlayer	Malaysia	2001:e68:540e:8258:9d0e:641b:12ef:efa6	rejected		
127	21	1	4074	Zium	Poland	89.149.68.50	approved		
128	22	20	13221	ð	USA	108.18.217.72	approved		
129	22	33	12083	ROMELY	Russia	2a03:f480:2:a::77	approved		Nitro, Wheelie Boost, Wings
130	9	33	12	Little Timmy	Romania	82.78.40.197	rejected		Fume Boost, Wheelie Boost, Wings
131	4	3	16199	Bir insan	Turkiye	159.146.9.114	approved		Fume Boost, Jump Shocks, Wheelie Boost, Wings
132	4	7	16197	Daf......	The Netherlands	2001:1c03:68d:e900:6c15:59ad:899c:5247	rejected		Coin Boost, Jump Shocks, Wheelie Boost, Wings
133	13	19	11799	Toast	Australia	2407:7000:b018:4100::100a	approved		Jump Shocks, Nitro, Overcharged Turbo, Wings
134	6	18	15260	ILLKA	Russia	2804:18:4872:f3f8:e8c9:b250:c4c8:4848	approved		Coin Boost, Fume Boost, Wings, Winter Tires
135	6	7	22499	Kosbow	Russia	2804:14d:5c80:9903:c9f4:31fa:d7ef:63d8	approved		Coin Boost, Jump Shocks, Landing Boost, Wings
136	6	15	27607	Peace	Czechia	2804:1b3:704e:8ed7:c9f4:31fa:d7ef:63d8	rejected		Coin Boost, Fume Boost, Landing Boost, Wings
137	10	14	45029	Miksu	Finland	2804:1b3:704e:8ed7:c9f4:31fa:d7ef:63d8	approved		Coin Boost, Jump Shocks, Landing Boost, Wings
138	10	33	32756	Peace	Czechia	2804:1b3:704e:8ed7:c9f4:31fa:d7ef:63d8	rejected		Coin Boost, Wheelie Boost, Wings
139	8	27	319752	3xtr3m3	poland	2804:1b3:704e:8ed7:c9f4:31fa:d7ef:63d8	approved		Coin Boost, Jump Shocks, Landing Boost, Magnet
140	8	20	39739	Matsentavra	Russia	62.167.165.11	rejected		Coin Boost, Fume Boost, Overcharged Turbo
141	9	10	19767	PG|誰か…		187.159.140.176	rejected		Fume Boost, Magnet, Wheelie Boost
142	9	1	70003	AUSTRAL	France	2a02:8428:af44:4401:a954:1619:29a6:c88b	rejected		Fume Boost, Jump Shocks, Landing Boost, Wings
143	19	19	3609	TGM	ð	2a02:c7c:c69d:6800:5cc1:23fa:40a8:7ca8	rejected		Fume Boost, Jump Shocks, Overcharged Turbo, Wings
144	2	2	13619	PR igifre2	Poland	188.137.73.208	rejected		Landing Boost, Wings, Winter Tires
145	17	14	10875	shady	Austria	83.215.115.54	rejected		Coin Boost, Fume Boost, Jump Shocks, Overcharged Turbo
146	17	21	10802	Kacp		83.215.115.54	approved		Coin Boost, Fume Boost, Jump Shocks, Overcharged Turbo
147	3	4	33467	sercz	china	2a0d:3341:b3ee:b610:b8ae:755f:f652:e92c	rejected		Jump Shocks, Thrusters, Wheelie Boost, Wings
148	4	27	11915	bluestar	Russia	2804:1b3:704e:b5ba:c9f4:31fa:d7ef:63d8	approved		Coin Boost, Fume Boost, Jump Shocks, Landing Boost
149	19	18	6767	Pls Titanium put me in your HCR2 STUPid scReeNshoTS Video ð	North Korea	79.230.107.39	rejected		Heavyweight, Magnet, Rollcage, Start Boost
150	1	5	16829	MV	Ireland	46.7.2.182	rejected		Coin Boost, Jump Shocks, Landing Boost, Wheelie Boost
151	18	27	94146	bluestar	Russia	2804:1b3:704e:b5ba:7c16:e88b:89ea:9587	approved		Coin Boost, Jump Shocks, Landing Boost, Magnet
152	9	21	84059	AUSTRAL	France	2a02:8428:af44:4401:c02b:c2b8:e840:fcd4	approved		Fume Boost, Jump Shocks, Landing Boost, Wings
153	15	31	20657	Djokovic		193.50.193.25	approved		Jump Shocks, Landing Boost, Nitro, Wings
154	13	31	20732	toast	Australia	119.18.0.189	rejected		Jump Shocks, Landing Boost, Nitro, Wings
155	13	25	15952	toast	Australia	119.18.0.189	approved		Coin Boost, Jump Shocks, Landing Boost, Nitro
156	13	29	16184	toast	Australia	119.18.0.189	approved		Jump Shocks, Landing Boost, Nitro, Wings
157	2	20	6089	Bryan8D	Australia	122.150.189.92	rejected		Fuel Boost, Landing Boost, Thrusters
158	2	27	17004	never be al9	India	103.189.143.174	rejected		Fume Boost, Jump Shocks, Landing Boost
218	12	21	16268	Kacp		95.49.115.75	rejected		Coin Boost, Jump Shocks, Landing Boost, Wings
159	8	26	16336	✅LIAM✅	USA	2600:1702:5350:1ee0:91f1:8d5f:9758:1286	rejected		Jump Shocks, Landing Boost, Wings
160	8	26	16366	✅LIAM✅	USA	2607:fb90:b550:cfa2:952c:3475:86ee:938	rejected		Jump Shocks, Landing Boost, Wings
161	21	9	4095	Silemer	Russia	128.14.37.80	approved		Fume Boost, Nitro, Wheelie Boost, Wings
162	22	31	12410	Dade	Libya	102.214.164.69	approved		Jump Shocks, Landing Boost, Nitro, Wings
163	11	28	9338	Ndwg	New Zealand	2407:7000:b018:4100::1002	approved		Landing Boost, Nitro, Wings, Winter Tires
164	11	4	23082	Ndwg	New Zealand	2407:7000:b018:4100::1002	approved		Fume Boost, Jump Shocks, Landing Boost, Wings
165	22	33	12091	Dade	Libya	102.214.164.86	approved		Fume Boost, Nitro, Wings
166	22	7	12563	Dade	Libya	102.214.164.72	rejected		Jump Shocks, Landing Boost, Nitro, Wings
167	22	23	12474	Dade	Libya	102.214.164.69	rejected		Jump Shocks, Landing Boost, Nitro, Wings
168	13	9	16388	toast	australia	119.18.0.189	rejected		Jump Shocks, Landing Boost, Nitro, Wings
169	21	31	5203	cysk	Brazil	83.85.206.91	rejected		Jump Shocks, Landing Boost, Wings, Winter Tires
170	13	7	16716	toast	Australia	119.18.0.189	rejected		Jump Shocks, Landing Boost, Nitro, Wings
171	17	31	10735	Kacp		95.49.89.237	rejected		Coin Boost, Fume Boost, Jump Shocks, Landing Boost
172	19	5	5720	Nikis	FI	86.60.234.178	rejected		Jump Shocks, Landing Boost, Wheelie Boost, Wings
173	15	8	20699	Nikis	FI	86.60.234.178	rejected		Fume Boost, Jump Shocks, Landing Boost, Wings
174	8	7	56178	Beast	Germany	2003:fb:8f4f:6586:7da6:7eb4:cd9f:6b68	rejected		Coin Boost, Jump Shocks, Landing Boost, Wings
175	13	23	19323	toast	Australia	119.18.0.189	rejected		Jump Shocks, Landing Boost, Nitro, Wings
176	11	27	71586	Ndwg	New Zealand	2407:7000:b018:4100::1004	rejected		Coin Boost, Jump Shocks, Landing Boost, Magnet
177	17	7	10723	Nikis	FI	86.60.234.178	rejected		Coin Boost, Jump Shocks, Landing Boost, Overcharged Turbo
178	2	20	19807	never be al9	India	2403:a080:411:706c:d059:b114:f0ce:89c9	rejected		Fuel Boost, Magnet, Nitro
179	21	31	5203	Cysk	https://youtu.be/1cX0UuigPP0?si=3-XjMAprpR_kg9TC	83.85.206.91	rejected		Jump Shocks, Landing Boost, Wings, Winter Tires
180	7	33	21256	why Pedro?	Czech republic	89.176.121.104	rejected		Landing Boost, Wheelie Boost, Wings
181	9	33	12	Little Timmy	Romania	82.76.245.177	rejected		Fume Boost, Wheelie Boost, Wings
182	19	19	3657	TGM	ð	2a02:c7c:c69d:6800:5b6:2827:acfa:8aae	rejected		Fume Boost, Jump Shocks, Overcharged Turbo, Wings
183	7	27	100020	Patbrick	UK	188.137.73.208	rejected		Coin Boost, Jump Shocks, Landing Boost
184	17	12	67	niggertitanium	PS	78.177.242.13	rejected		Afterburner, Air Control, Fuel Boost, Rollcage
185	16	30	6475	Najmichalko	Slovakia	2a00:1028:83ce:1352:9156:b79d:4644:48ed	rejected		Coin Boost, Fume Boost, Landing Boost, Wheelie Boost
186	3	3	67	hi titanium your shit sucks nipatsu you too you guys vibecode shit lol	hi titanium your shit sucks nipatsu you too you guys vibecode shit lol	104.28.192.51	rejected		Afterburner, Coin Boost, Fuel Boost
187	11	13	67	titanium gayming hcr6	france	193.50.193.25	rejected		Afterburner, Fuel Boost, Nitro, Start Boost
188	22	14	12567	toast	Australia	119.18.0.189	rejected		Jump Shocks, Landing Boost, Nitro, Wings
189	11	16	10489	Ndwg	New Zealand	2407:7000:b018:4100::1004	rejected		Coin Boost, Fume Boost, Magnet, Nitro
190	10	33	32787	cysk	brazil	2804:1b3:704e:977a:351a:6ed0:9061:a6de	rejected		Coin Boost, Fume Boost, Wings
191	4	28	12302	Ndwg	New Zealand	2407:7000:b018:4100::1004	approved		Coin Boost, Fume Boost, Wings, Winter Tires
192	17	29	10670	Zorro	Germany	83.215.115.54	approved		Coin Boost, Fume Boost, Jump Shocks, Overcharged Turbo
193	14	20	12400	Nasa PC	USA	2407:7000:b018:4100::1004	approved		Coin Boost, Jump Shocks, Landing Boost, Wings
194	8	26	16366	✅LIAM✅		2600:1702:5350:1ee0:c5e0:8f4c:f224:a221	rejected		Jump Shocks, Landing Boost, Wings
195	1	27	14041	SkR|glidegod	Sweden	81.234.156.254	rejected		Jump Shocks, Landing Boost, Magnet
196	19	19	3726	TGM	ð	2a02:c7c:c69d:6800:c022:248c:3206:e71a	approved		Fume Boost, Jump Shocks, Overcharged Turbo, Wings
197	4	27	12336	Ndwg	New Zealand	119.18.0.189	rejected		Coin Boost, Fume Boost, Jump Shocks, Landing Boost
198	12	27	25162	Ndwg	New Zealand	2407:7000:b018:4100::100a	approved		Coin Boost, Jump Shocks, Landing Boost, Magnet
199	21	4	3667	Ndwg	New Zealand	2407:7000:b018:4100::100a	approved		Jump Shocks, Nitro, Thrusters, Wings
200	14	4	11863	Ndwg	New Zealand	2407:7000:b018:4100::100a	rejected		Jump Shocks, Landing Boost, Nitro, Wings
201	20	11	4740	Zombix	Poland	2a00:1858:1054:8aee:f0d9:caf8:c323:3b18	rejected		Nitro, Thrusters, Wheelie Boost, Wings
202	8	6	20000	Tx		146.196.50.212	rejected		Fume Boost, Jump Shocks, Landing Boost, Wings
203	21	24	4095	Levi	Ukraine	2a00:1858:1054:8aee:45c4:c897:da7c:fbee	rejected		Jump Shocks, Wheelie Boost, Wings, Winter Tires
204	7	20	9246	Bryan8D	Australia	122.150.189.168	rejected		Jump Shocks, Landing Boost, Wings
205	21	31	5203	cysk	Finland	2402:8100:2b81:b4c0::1761:ccce	rejected		Jump Shocks, Landing Boost, Wings, Winter Tires
206	17	27	14966	ð	USA	2601:980:4200:5300:188b:f584:46d2:209f	approved		Coin Boost, Jump Shocks, Landing Boost, Magnet
207	16	29	12721	German cb	Germany	2001:861:8050:5ba0:8ae3:a416:fb65:b07	rejected		Jump Shocks, Landing Boost, Nitro, Wings
208	2	27	144245	Stormy	Singapore ð	154.5.120.228	rejected		Jump Shocks, Landing Boost, Magnet
209	22	27	19451	no name (no, seriously, this player has no name)	Finland ð	154.5.120.228	rejected		Jump Shocks, Landing Boost, Magnet
210	2	20	19806	(PR)AJ	USA	2601:601:d087:48e0:aa30:55af:8111:24eb	rejected		Coin Boost, Magnet, Winter Tires
211	19	19	4161	TGM	ð	2a02:c7c:c69d:6800:a9a0:d39c:c1ba:1cdc	approved		Fume Boost, Jump Shocks, Overcharged Turbo, Wings
212	6	31	4650	bbyde	Philippines	2405:8d40:4042:f935:6996:71dc:6e23:edf1	rejected		Fume Boost, Magnet, Winter Tires
213	11	11	10509	Ndwg	New Zealand	2407:7000:b018:4100::100a	rejected		Coin Boost, Fume Boost, Wheelie Boost, Wings
214	10	27	34843	TPSG6572	Philippines	175.176.28.246	rejected		Jump Shocks, Landing Boost, Magnet
215	17	14	10876	Joplin	USA	108.18.217.72	approved		Coin Boost, Fume Boost, Jump Shocks, Overcharged Turbo
216	21	7	4676	Kacp	Poland	2a00:1858:1054:8aee:91be:178e:429f:3342	approved		Jump Shocks, Landing Boost, Wheelie Boost, Wings
217	12	14	17022	Kacp		95.49.115.75	rejected		Jump Shocks, Landing Boost, Wheelie Boost, Wings
219	19	34	5080	Nikis	FI	86.60.234.178	rejected		Fume Boost, Jump Shocks, Wings
220	19	34	5368	Nikis	FI	86.60.234.178	rejected		Jump Shocks, Landing Boost, Wings
221	4	33	18570	K4H	Russia	2a12:bec4:1be0:e64::1	rejected		Fume Boost, Wheelie Boost, Wings
222	2	20	91404	K4H	Russia	2a12:bec4:1be0:e64::1	rejected		Coin Boost, Jump Shocks, Landing Boost, Wings
223	9	34	95791	Nikis	FI	86.60.234.178	rejected		Jump Shocks, Landing Boost, Wings
224	4	34	10521	Myron	Uzbekistan ð	84.54.73.165	approved		Coin Boost, Wings, Winter Tires
225	20	34	4724	RStokey	USA	2601:603:5280:cc70:d04:a875:d01d:586a	rejected		Jump Shocks, Landing Boost, Wings
226	21	34	3477	RStokey	USA	2601:603:5280:cc70:d04:a875:d01d:586a	rejected		Jump Shocks, Landing Boost, Wings
227	5	33	31650	Humood	Saudi Arabia	188.53.221.234	approved		Fume Boost, Nitro, Overcharged Turbo, Wings
228	8	32	26034	{CH}=DeMoN	India	2405:201:9006:71e5:bd86:6a3c:afe9:720f	rejected		Jump Shocks, Landing Boost, Wings
229	19	34	5718	Nikis	Fi	86.60.234.178	rejected		Jump Shocks, Landing Boost, Wings
230	11	34	23084	Ndwg	New Zealand	2407:7000:b018:4100::1006	rejected		Jump Shocks, Landing Boost, Wings
231	22	16	12060	Ndwg	New Zealand	2407:7000:b018:4100::1006	rejected		Coin Boost, Fume Boost, Magnet, Nitro
232	8	28	10929	ok	Philippines	112.206.241.193	rejected		Coin Boost, Fume Boost, Nitro, Wings
233	5	34	16239	Arthaud	france	2001:861:8050:5ba0:8176:b157:ed2a:8398	rejected		Jump Shocks, Landing Boost, Wings
234	22	34	13221	Dade	Libya	102.214.164.66	rejected		Jump Shocks, Landing Boost, Wings
235	22	34	13224	Dade	Libya	102.214.164.75	rejected		Jump Shocks, Landing Boost, Wings
236	6	34	22500	ARTHUR	france	2001:861:8050:5ba0:fc09:94aa:5a33:fcd3	rejected		Jump Shocks, Landing Boost, Wings
237	10	33	34852	For Dragon	Syria	5.155.97.243	rejected		Coin Boost, Fume Boost, Landing Boost, Wings
238	5	34	53632	Humood	Saudi Arabia	188.53.220.233	rejected		Jump Shocks, Landing Boost, Wings
239	7	27	22936	Herdyu☆	U.S	2607:fb90:cf24:7a3:6c07:c9d0:416f:ac3d	rejected		Jump Shocks, Landing Boost, Magnet
240	8	34	144724	Nikis	FI	83.245.235.180	rejected		Jump Shocks, Landing Boost, Wings
241	6	32	19186	DanioDuck	Netherlands	2407:7000:b018:4100::1003	rejected		Jump Shocks, Landing Boost, Wings
242	14	28	10446	Ndwg	New Zealand	2407:7000:b018:4100::1007	rejected		Coin Boost, Landing Boost, Nitro, Wings
243	5	34	70293	Humood	Saudi Arabia	188.53.230.121	rejected		Jump Shocks, Landing Boost, Wings
244	20	23	5942	Stu	Saudi Arabia	188.53.230.121	rejected		Jump Shocks, Spoiler, Wings, Winter Tires
245	21	4	3828	cysk	Brazil, full recording available: https://youtu.be/UuRg9BPKipc?si=dCsX_2FF6pg6Rafy	2804:1b3:704e:8e10:bcdd:8d1d:b4c9:1f1b	rejected		Jump Shocks, Landing Boost, Wings, Winter Tires
246	17	34	10675	Zorro	Germany	83.215.115.54	approved		Jump Shocks, Landing Boost, Wings
247	22	14	12567	Stu	Saudi Arabia	151.255.82.89	rejected		Jump Shocks, Landing Boost, Wings
248	8	33	39739	ꛕꚶㄗð¢§	Brazil	2804:14d:4cd5:81ba:cd19:d789:aff8:5bea	rejected		Coin Boost, Landing Boost, Wheelie Boost, Wings
249	6	33	27524	ꛕꚶㄗð¢§	Brazil	2804:14d:4cd5:81ba:cd19:d789:aff8:5bea	rejected		Coin Boost, Fume Boost, Landing Boost, Wings
250	9	33	20756	:]	Indonesia	118.137.62.83	rejected		Nitro, Overcharged Turbo, Wings
251	8	34	160236	Beast	Germany	2003:fb:8f38:e515:55a3:ce46:8437:7ac1	rejected		Jump Shocks, Landing Boost, Wings
252	22	31	12458	Nakkibiilo	Finland	102.214.164.66	rejected		Jump Shocks, Landing Boost, Nitro, Wings
253	10	33	33554	Stu	Saudi Arabia	151.255.95.44	rejected		Coin Boost, Landing Boost, Wings
254	9	17	26200	Nikis	Fi	87.236.224.77	rejected		Coin Boost, Landing Boost, Overcharged Turbo, Wings
255	19	14	5132	Stu	Saudi Arabia	151.255.95.44	rejected		Jump Shocks, Landing Boost, Overcharged Turbo, Wings
256	19	25	1654	CE|AJ	USA	2601:601:d087:48e0:568f:7306:6f0b:f877	rejected		Coin Boost, Jump Shocks, Landing Boost
257	10	14	45092	Stu		151.255.95.44	rejected		Coin Boost, Jump Shocks, Landing Boost, Wings
258	5	32	16391	Humood	Saudi Arabia	151.255.95.44	rejected		Jump Shocks, Landing Boost, Nitro, Wings
259	8	4	98512	Aky1236		2401:4900:a132:f427:66e5:6634:849b:3892	rejected		Coin Boost, Jump Shocks, Landing Boost, Wings
260	18	34	64017	Beast	Germany	2003:fb:8f38:e585:9c30:9294:81bd:85a4	rejected		Jump Shocks, Landing Boost, Wings
261	11	31	29363	Ndwg	New Zealand	2407:7000:b018:4100::100a	rejected		Coin Boost, Jump Shocks, Landing Boost, Wings
262	4	14	14588	Stu (formerly known as bucke jr)	US (for whatever reason using saudi arabia flag on that account though)	2804:1b3:704e:a587:40b4:127a:5a7a:7110	rejected		Coin Boost, Fume Boost, Wheelie Boost, Wings
263	11	21	29435	Ndwg	New Zealand	119.18.0.189	rejected		Coin Boost, Jump Shocks, Landing Boost, Wings
264	13	21	20732	toast	Australia	119.18.0.189	rejected		Jump Shocks, Landing Boost, Nitro, Wings
265	22	25	12063	Ndwg	New Zealand	119.18.0.189	rejected		Coin Boost, Jump Shocks, Landing Boost, Nitro
266	4	7	16233	yazi	USA	100.16.11.231	rejected		Coin Boost, Fume Boost, Wheelie Boost, Wings
267	14	15	11849	Ndwg	New Zealand	2407:7000:b018:4100::1008	rejected		Fume Boost, Nitro, Wheelie Boost, Wings
268	11	26	23085	Miksu	Finland	2407:7000:b018:4100::1008	rejected		Coin Boost, Jump Shocks, Landing Boost, Wings
269	17	14	10885	Stu	Saudi Arabia	151.255.95.34	rejected		Coin Boost, Fume Boost, Jump Shocks, Overcharged Turbo
270	13	5	20742	toast	Australia	119.18.0.189	rejected		Jump Shocks, Landing Boost, Nitro, Wings
271	22	31	12738	Dade	Libya	102.214.164.69	rejected		Jump Shocks, Landing Boost, Nitro, Wings
272	10	34	130368	Beast	Germany	2003:fb:8f38:e501:e4d2:e38f:ed8f:c5de	rejected		Jump Shocks, Landing Boost, Wings
273	4	25	12363	yazi	USA	100.16.11.231	rejected		Coin Boost, Fume Boost, Landing Boost, Winter Tires
274	13	8	21072	toast	Australia	119.18.0.189	rejected		Jump Shocks, Landing Boost, Nitro, Wings
275	18	34	77679	DanioDuck	Netherlands	2a02:a44d:4e70:0:d9ae:a3:2bc9:9429	rejected		Jump Shocks, Landing Boost, Wings
276	7	33	21598	Humood	Saudi Arabia	151.255.95.34	rejected		Coin Boost, Landing Boost, Nitro, Wings
277	15	10	22077	K.RAVVVV	Azerbaijan	94.120.138.218	rejected		Fume Boost, Jump Shocks, Nitro, Wings
278	4	31	18039	Stu	Saudi Arabia	188.53.53.208	rejected		Coin Boost, Jump Shocks, Landing Boost, Wings
279	4	21	16637	Stu	Saudi Arabia	188.53.53.208	rejected		Coin Boost, Landing Boost, Wings, Winter Tires
280	4	27	12382	Stu	Saudi Arabia	188.53.53.208	rejected		Coin Boost, Fume Boost, Jump Shocks, Landing Boost
281	4	13	14256	Stu	Saudi Arabia	188.53.53.208	rejected		Coin Boost, Wheelie Boost, Wings, Winter Tires
282	4	9	15765	yazi	USA	100.16.11.231	approved		Coin Boost, Jump Shocks, Wheelie Boost, Wings
\.


--
-- Data for Name: _player; Type: TABLE DATA; Schema: public; Owner: rebasedata
--

COPY public._player ("idPlayer", "namePlayer", country) FROM stdin;
0	___	___
1	Zorro	Germany
2	Kosbow	Russia
3	Illka	Russia
4	HCR2GUY	Norway
5	Lucas	France
6	DaBell	Australia
7	Crash77	USA
8	Feifei	China
9	Bir Insan	Turkiye
10	Ndwg	New Zealand
11	lpg	Brazil
12	JumboVisma	Slovenia
13	Cute	Germany
14	MaxiGaming	Argentina
15	Nasa PC	USA
16	FunkyFries	New Zealand
17	El Chiquitin	Argentina
18	Zeus	Belgium
19	Markus	Austria
20	Sabeer	USA
21	Raiden	Austria
22	DanioDuck	Netherlands
23	Delta	Romania
24	Kacp	Poland
25	Chip	France
26	Djokovic	Serbia
27	Plazma	Serbia
28	Lebest	France
29	Zium	Poland
30	Jemo	USA
31	Adam	Algeria
32	Isalriz	Sweden
33	PetrosG	Greece
34	Krecek	Czechia
35	Patbrick	UK
36	Hedgehog	UK
37	Happy	Poland
38	Toast	Australia
39	Mujigae	Russia
40	ZoroxVN	Vietnam
41	BadAtHcr	Netherlands
42	Carlos	Brazil
43	Pgy	China
44	MonoVictor	Ireland
45	Sporty	Russia
46	Miksu	Finland
47	Bomber	Finland
48	TGM	UK
49	Volic	Poland
50	BlackyNeko	Indonesia
51	Synix	France
52	Pikachu	Poland
53	Nikis	Finland
54	Levi	Ukraine
55	DAJ	USA
56	Tobisus	Ireland
57	DrFlask	Sweden
58	Narvik-Berra	Sweden
59	Cobus	Netherlands
60	ZombiX	Poland
61	SebiStein	Romania
62	Racer60604	Romania
63	Bimi	Albania
64	Heio Leo	USA
65	DaGoat	Russia
66	NaturalWinner	China
67	Gusgus	USA
68	Lega	Ukraine
69	AnonimChik	Russia
70	XvGG	Malaysia
71	Celsius	Romania
72	Dusty	Canada
73	Can Tapanc	Turkiye
74	Gazou	France
75	Treky	Australia
76	Bucke jr	USA
77	Hyped	New Zealand
78	Amiguim	Brazil
79	Chili	USA
80	Eric	Germany
81	Mapleshade	Sweden
82	Dubstep	Russia
83	Yonatanking	Israel
84	Referee	Serbia
85	Raking	Russia
86	SteenDeSten	Netherlands
87	SS	Estonia
88	Gamerbro44	Canada
89	V2V4	France
90	Rocket	UK
91	Nevnev	Switzerland
92	Jeda	Netherlands
93	Atlas	USA
94	MarkaVar	Lithuania
95	TocaADR	Philippines
96	DinklySquink	UK
97	Yanix	Russia
98	Linus	Germany
99	MJD	Syria
100	Chinese Version	China
101	TryWR	Germany
102	Arnaud	Canada
103	Michi2	Germany
104	Lyewaz	France
105	Yazi	USA
106	BotLogic	Russia
107	Cyan Skull	Brazil
108	Evenub	Australia
109	Danya	Ukraine
110	Brrr	Ukraine
111	Temu Cute	China
112	lucas64	France
113	Lore	Italy
114	Nakkibiilo	Finland
115	GEN	Germany
116	Omega	Poland
117	Blake	Australia
118	Mushroom	Russia
119	Kuba	Poland
120	Joplin	USA
121	Zoda	Belgium
122	Humood	Saudi Arabia
123	Yoyo14	France
124	Puma	Austria
125	Vereshchak	Ukraine
126	Rico	UK
127	Rolo	Hungary
128	Rick Tripledick	USA
129	Speed Michi	Austria
130	Element	Australia
131	Zephyro	Poland
132	3XTR3M3	Poland
133	Oscar	USA
134	Peace	Czechia
135	Tale	Belgium
136	Kurt	Iran
137	Antonio97	Estonia
138	BILETOWYCH	Poland
139	CaptainJack	Slovakia
140	Pigeon	Poland
141	Vynix	USA
142	Hill Driver	Turkiye
143	CEO	Germany
144	zZolker	Uzbekistan
145	Speedy	Austria
146	IceDragonVN	Vietnam
147	Kova	Bosnia and Herzegovina
148	Driver05	Italy
149	Kylian	France
150	Rejuvenated	USA
151	Alex	France
152	Nicu	Romania
153	FastWHY	Czechia
154	PowerCat	Russia
155	Chips	UK
156	Ben Bro	Australia
157	MACES	Turkiye
158	Kistek	Poland
159	Berni	Germany
160	AUSTRAL	France
161	RUR	Israel
162	Supanat	Thailand
163	Titanium	France
164	Nipatsu	Finland
165	Noobmaster69	France
166	Oganesson	Turkiye
167	Gabs	Switzerland
168	Lite	Russia
169	Flecka	Philippines
170	m.m	France
171	Finteam	Finland
172	Ashley	Vietnam
173	John	USA
174	Xamier	Austria
175	Fridge	USA
176	Bambi	Germany
177	Entripse	Russia
178	Lucas14	Brazil
179	RAWDAWG	USA
180	Dade	Libya
181	Hille	Germany
182	ARTHUR	France
183	Steve	UK
184	Lucas64	France
185	Stu	Saudi Arabia
186	german cb	Germany
187	Zoobaman	Canada
188	Regotn	China
189	MonoDuy	Vietnam
190	InkoEX	Australia
191	Heat	India
192	TORTU	Canada
193	nswt-bjty	Czechia
194	Advantoer	USA
195	Zandrik	Russia
196	Huang Tang Ming	China
197	Hillovilperi	Finland
198	ihatethismap	Latvia
199	Arcun Ranger	New Zealand
200	COLA	China
201	Bir insan	Turkiye
202	ROMELY	Russia
203	ð	USA
204	ILLKA	Russia
205	zhihe0848	China
206	3xtr3m3	poland
207	bluestar	Russia
208	toast	Australia
209	Billy 900	UK
210	Evgplays	Norway
211	Whaahhh!!	Netherlands
212	no name	China
213	Silemer	Russia
214	Weirdo	USA
215	Najmichalko	Slovakia
216	HUNGREEN	Japan
217	shriktic	New Zealand
218	mikey 10	Saint Vincent and the Grenadines
219	FelixCraft	Germany
220	Kanye4Here	Russia
221	Aiden ð	USA
222	ð Ice Snow	China
223	⚓ Asuka	China
224	Ultimate	Ukraine
225	пысюнчи	Russia
226	star83012	Thailand
227	Myron	Uzbekistan
228	self-legend	USA
229	Arthaud	France
230	3AMER	Jordan
231	Ник Чит	Russia
232	DarkFall	Russia
233	Theo!!	Russia
234	distortion42	Russia
235	[AR]-ZY	China
236	RStokey	USA
237	Roman	Russia
238	Gui HCR2	Brazil
239	speed :)	Canada
240	Nikaru Hakamura	Albania
241	Whitehorse	Antarctica
242	Obi	Finland
243	Vułcan	India
244	SaMueL	UK
245	CreeperMan	Syria
246	Phoenix	USA
247	ꛕꚶㄗð¢§	Brazil
248	Beast	Germany
249	Zhyprin	Philippines
250	Infiltrate	China
251	ðFai	China
252	yazi	USA
\.


--
-- Data for Name: _sqlite_sequence; Type: TABLE DATA; Schema: public; Owner: rebasedata
--

COPY public._sqlite_sequence (name, seq) FROM stdin;
PendingSubmission	282
News	33
\.


--
-- Data for Name: _tuningpart; Type: TABLE DATA; Schema: public; Owner: rebasedata
--

COPY public._tuningpart ("idTuningPart", "nameTuningPart") FROM stdin;
19	Afterburner
18	Air Control
8	Coin Boost
11	Flip Boost
10	Fuel Boost
12	Fume Boost
16	Heavyweight
7	Jump Shocks
3	Landing Boost
2	Magnet
5	Nitro
4	Overcharged Turbo
13	Rollcage
14	Spoiler
6	Start Boost
15	Thrusters
9	Wheelie Boost
1	Wings
17	Winter Tires
\.


--
-- Data for Name: _tuningsetup; Type: TABLE DATA; Schema: public; Owner: rebasedata
--

COPY public._tuningsetup ("idTuningSetup") FROM stdin;
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108
109
110
111
112
113
114
115
116
117
118
119
120
121
122
123
124
125
126
127
128
129
130
131
132
133
134
135
136
137
138
139
140
141
142
143
144
145
146
147
148
149
150
151
152
153
154
155
156
157
158
159
160
161
162
163
164
165
166
167
168
169
170
171
172
173
174
175
176
\.


--
-- Data for Name: _tuningsetupparts; Type: TABLE DATA; Schema: public; Owner: rebasedata
--

COPY public._tuningsetupparts ("idTuningSetup", "idTuningPart") FROM stdin;
1	1
1	3
1	5
1	7
2	1
2	3
2	7
2	9
3	1
3	3
3	7
3	8
4	1
4	3
4	7
4	11
5	1
5	9
5	12
5	17
6	1
6	5
6	8
6	9
7	1
7	5
7	9
7	12
8	1
8	5
8	8
8	9
9	2
9	8
9	9
9	12
10	1
10	7
10	16
10	17
11	1
11	7
11	9
11	12
12	2
12	3
12	7
12	8
13	3
13	5
13	7
13	8
14	1
14	5
14	8
14	15
15	1
15	4
15	7
15	8
16	1
16	3
16	7
16	13
17	1
17	2
17	5
17	8
18	2
18	5
18	8
18	12
19	4
19	5
19	8
19	12
20	1
20	3
20	8
20	12
21	1
21	2
21	3
21	8
22	1
22	3
22	8
22	17
23	1
23	4
23	5
23	8
24	2
24	3
24	8
24	17
25	3
25	7
25	8
25	17
26	2
26	3
26	7
26	17
27	3
27	5
27	7
27	17
28	1
28	7
28	9
28	12
29	1
29	3
29	5
30	1
30	3
30	7
30	12
31	1
31	4
31	7
31	12
32	1
32	9
32	12
33	1
33	8
33	9
33	12
34	4
34	7
34	8
34	12
35	3
35	7
35	8
35	12
36	1
36	3
36	7
37	1
37	3
37	7
37	17
38	1
38	3
38	4
38	7
39	3
39	5
39	7
39	8
40	4
40	7
40	8
40	12
41	2
41	4
41	5
41	12
42	1
42	7
42	8
42	9
43	1
43	4
43	8
44	1
44	5
44	7
44	10
45	1
45	4
45	8
45	12
46	3
46	8
46	9
46	12
47	1
47	5
47	7
47	12
48	1
48	8
48	9
48	17
49	1
49	5
49	7
49	17
50	1
50	5
50	7
50	9
51	1
51	7
51	15
51	17
52	1
52	8
52	9
53	1
53	5
53	9
53	17
54	1
54	2
54	7
55	1
55	2
55	12
55	15
56	1
56	7
56	8
56	15
57	1
57	3
57	4
57	8
58	3
58	7
58	8
59	1
59	7
59	8
59	17
60	1
60	7
60	16
60	17
61	1
61	3
61	5
61	17
62	1
62	3
62	9
62	17
63	4
63	5
63	7
63	12
64	1
64	2
64	8
65	4
65	8
65	9
65	12
66	1
66	3
66	5
66	8
67	6
67	14
67	18
67	19
68	1
68	5
68	7
68	15
69	1
69	7
69	8
69	12
70	1
70	3
70	8
70	17
71	1
71	9
71	15
71	17
72	1
72	9
72	12
72	17
73	1
73	3
73	5
73	12
74	1
74	4
74	13
74	17
75	1
75	5
75	9
75	12
76	1
76	3
76	7
76	15
77	3
77	5
77	7
77	17
78	5
78	8
78	9
79	3
79	4
79	7
79	8
80	1
80	3
80	9
81	1
81	3
81	4
81	9
82	1
82	3
82	5
82	17
83	1
83	3
83	7
83	12
84	1
84	5
84	12
85	1
85	3
85	5
85	7
86	1
86	8
86	9
87	1
87	8
87	12
87	17
88	1
88	7
88	12
88	15
89	2
89	8
89	12
89	13
90	1
90	3
90	9
90	12
91	1
91	3
91	5
91	15
92	1
92	3
92	8
93	1
93	9
93	16
94	1
94	5
94	7
94	8
95	1
95	5
95	8
95	12
96	1
96	3
96	8
96	15
97	3
97	7
97	8
97	9
98	1
98	8
98	12
98	17
99	4
99	7
99	8
99	12
100	1
100	3
100	7
100	8
101	1
101	3
101	5
101	8
102	1
102	2
102	3
102	5
103	2
103	3
103	7
103	8
104	1
104	4
104	7
104	12
105	1
105	7
105	15
106	1
106	3
106	4
107	1
107	3
107	4
107	12
108	1
108	4
108	5
108	9
109	7
109	8
109	9
109	12
110	1
110	3
110	5
110	9
111	1
111	5
111	8
112	1
112	5
112	15
113	1
113	5
113	7
113	15
114	1
114	3
114	5
114	13
115	1
115	5
115	9
116	1
116	4
116	7
116	15
117	1
117	7
117	12
117	13
118	3
118	5
118	7
118	12
119	8
119	9
119	12
120	5
120	8
120	9
120	12
121	1
121	5
121	9
121	15
122	1
122	3
122	8
122	9
123	1
123	2
123	3
123	7
124	1
124	7
124	10
124	17
125	8
125	12
125	17
126	1
126	4
126	5
126	13
127	1
127	7
127	9
127	17
128	3
128	8
128	9
128	12
129	1
129	7
129	14
129	17
130	1
130	8
130	12
131	2
131	5
131	10
131	12
132	1
132	3
132	4
132	5
133	2
133	3
133	8
133	12
134	2
134	3
134	8
135	1
135	4
135	5
135	7
136	1
136	3
136	9
136	15
137	1
137	7
137	12
137	15
138	1
138	5
138	8
139	1
139	2
139	5
139	8
140	1
140	8
140	9
140	17
141	1
141	7
141	8
142	1
142	3
142	8
143	1
143	2
143	5
144	1
144	12
144	17
145	1
145	5
145	8
145	17
146	1
146	3
146	12
146	17
147	1
147	2
147	3
147	5
148	1
148	5
148	7
148	13
149	2
149	8
149	12
150	1
150	5
150	8
150	17
151	1
151	4
151	10
151	17
152	2
152	3
152	7
152	8
153	1
153	7
153	8
153	12
154	1
154	5
154	9
154	12
155	8
155	9
155	12
156	1
156	4
156	7
156	12
157	1
157	5
157	12
157	17
158	4
158	8
158	9
159	4
159	7
159	8
159	12
160	1
160	3
160	7
160	9
161	1
161	2
161	5
162	1
162	7
162	12
163	1
163	8
163	17
164	4
164	5
164	8
164	9
165	2
165	5
165	8
165	13
166	1
166	4
166	5
166	12
167	1
167	9
167	17
168	1
168	9
168	10
168	17
169	1
169	4
169	9
169	17
170	7
170	16
170	17
171	8
171	9
171	17
172	1
172	2
172	7
173	1
173	3
173	7
174	1
174	5
174	7
174	9
175	3
175	8
175	12
175	17
176	1
176	7
176	8
176	9
\.


--
-- Data for Name: _vehicle; Type: TABLE DATA; Schema: public; Owner: rebasedata
--

COPY public._vehicle ("idVehicle", "nameVehicle") FROM stdin;
1	Hill Climber
2	Scooter
3	Bus
4	Hill Climber Mk2
5	Tractor
6	Motocross
7	Dune Buggy
8	Sports Car
9	Monster Truck
10	Rock Bouncer
11	Rotator
12	Super Diesel
13	Chopper
14	Tank
15	Snowmobile
16	Hoverbike
17	Lowrider
18	Beast
19	Monowheel
20	Rally Car
21	Raider
22	Formula
23	Muscle Car
24	Racing Truck
25	Hotrod
26	CC-EV
27	Glider
28	Superbike
29	Supercar
30	Moonlander
31	Bolt
32	ATV
33	Offroader
34	Stocker
\.


--
-- Data for Name: _worldrecord; Type: TABLE DATA; Schema: public; Owner: rebasedata
--

COPY public._worldrecord ("idMap", "idVehicle", "idPlayer", distance, current, "idTuningSetup", questionable, questionable_reason) FROM stdin;
1	13	6	20413	1	20	0	
1	24	6	20541	1	2	0	
2	1	126	40064	1	3	0	
2	6	30	56881	1	4	0	
2	8	2	42719	1	3	0	
2	12	2	52026	1	36	0	
3	2	3	25373	1	76	0	
3	6	3	27651	1	76	0	
3	13	3	25637	1	96	0	
3	19	3	20524	1	88	0	
3	24	3	25695	1	56	0	
3	29	13	19662	1	141	0	
4	5	3	14421	1	48	0	
4	8	1	14411	1	11	0	
4	24	105	18485	1	72	0	
5	3	32	40451	1	1	0	
5	5	32	49173	1	1	0	
5	11	16	22500	1	86	0	
5	17	32	19816	1	73	0	
5	20	32	70542	1	36	0	
6	5	2	34167	1	3	0	
6	11	1	16647	1	130	0	
6	13	2	30793	1	20	0	
6	17	2	16650	1	70	0	
6	20	2	46759	1	36	0	
6	24	2	34044	1	2	0	
7	1	7	24856	1	1	0	
7	2	30	30477	1	1	0	
7	3	7	39910	1	1	0	
7	7	7	23866	1	36	0	
7	8	7	24841	1	3	0	
7	9	30	21345	1	3	0	
7	10	7	21626	1	2	0	
7	11	1	21287	1	86	0	
7	13	17	21580	1	90	0	
7	17	7	21546	1	66	0	
7	19	7	14643	1	135	0	
7	21	7	39903	1	36	0	
7	22	7	19789	1	37	0	
7	24	7	21703	1	1	0	
7	26	7	65614	1	36	0	
7	30	7	9458	1	46	0	
7	31	7	28807	1	36	0	
8	3	14	104819	1	3	0	
8	7	14	56176	1	36	0	
8	8	5	125173	1	3	0	
8	11	16	39374	1	111	0	
8	13	14	63098	1	20	0	
8	17	48	39222	1	57	0	
8	18	14	40022	1	94	0	
8	24	70	73543	1	3	0	
8	26	5	406911	1	3	0	
9	2	53	67135	1	3	0	
9	9	53	67155	1	3	0	
9	11	16	47157	1	52	0	
9	17	29	26200	1	57	0	
9	19	48	30100	1	15	0	
9	24	60	85758	1	3	0	
10	11	16	21106	1	142	0	
10	12	5	45050	1	36	0	
10	13	5	25970	1	20	0	
10	17	5	21089	1	20	0	
10	18	14	21087	1	69	0	
10	19	88	16977	1	31	0	
10	24	5	45039	1	3	0	
10	26	22	117484	1	36	0	
11	13	10	10422	1	110	0	
11	24	10	22329	1	2	0	
12	3	51	15259	1	30	0	
12	6	22	16269	1	4	0	
12	8	5	13984	1	30	0	
12	17	1	11612	1	20	0	
12	24	24	14178	1	2	0	
13	1	30	21569	1	1	0	
13	2	30	23736	1	36	0	
13	12	38	20732	1	1	0	
13	13	109	16183	1	66	0	
13	27	38	46643	1	58	0	
14	5	71	11899	1	3	0	
14	13	17	11883	1	90	0	
14	17	1	10503	1	101	0	
14	24	1	12405	1	2	0	
14	26	20	12272	1	36	0	
15	2	1	20699	1	36	0	
15	3	17	22397	1	1	0	
15	8	20	20699	1	30	0	
15	11	16	22081	1	138	0	
15	26	20	58836	1	36	0	
15	30	6	8665	1	134	0	
16	1	5	16735	1	1	0	
16	2	30	16131	1	1	0	
16	8	20	16697	1	30	0	
16	11	1	12197	1	92	0	
16	17	2	13483	1	66	0	
16	24	5	15829	1	3	0	
16	26	5	18142	1	36	0	
17	3	1	11235	1	109	0	
17	6	1	11850	1	4	0	
17	8	1	10698	1	35	0	
17	24	1	11231	1	65	0	
18	1	6	43901	1	36	0	
18	7	10	35943	1	36	0	
18	10	24	24096	1	2	0	
18	11	1	13315	1	52	0	
18	12	78	36279	1	36	0	
18	19	1	12775	1	31	0	
18	23	20	36008	1	36	0	
18	24	24	35664	1	2	0	
18	30	6	9306	1	119	0	
19	1	1	5365	1	30	0	
19	2	1	5638	1	37	0	
19	8	1	5079	1	2	0	
19	10	1	6526	1	50	0	
20	1	1	4741	1	47	0	
20	3	7	4745	1	137	0	
20	5	1	5051	1	117	0	
20	13	6	4722	1	121	0	
20	19	6	4721	1	116	0	
20	30	6	3847	1	9	0	
21	2	1	4675	1	37	0	
21	5	6	4388	1	37	0	
21	6	1	3854	1	76	0	
21	8	1	3791	1	50	0	
21	11	16	3530	1	112	0	
21	13	1	3792	1	91	0	
21	17	28	3788	1	144	0	
21	19	1	3825	1	116	0	
21	26	1	4100	1	37	0	
21	30	6	3684	1	46	0	
7	8	20	15646	0		0	
7	10	1	21347	0		0	
8	17	138	17724	0		0	
18	10	1	13483	0		0	
19	10	1	4791	0		0	
11	12	46	23079	1	30	0	
8	32	143	65572	1	36	0	
10	32	22	44410	1	36	0	
13	32	38	17967	1	36	0	
12	32	22	12254	1	36	0	
11	32	24	26286	1	36	0	
22	30	29	6582	1	133	0	
19	28	31	4035	1	53	0	
12	16	119	10982	1	19	0	
18	32	145	31481	1	36	0	
1	21	6	19005	1	3	0	
21	28	24	3508	1	53	0	
15	32	31	15100	1	36	0	
17	16	1	11034	1	19	0	
21	29	24	3824	1	124	0	
20	28	24	4707	1	53	0	
22	17	148	12073	1	66	0	
8	4	143	79119	1	3	0	
1	9	6	17467	1	3	0	
1	4	6	15252	1	3	0	
1	6	6	22963	1	4	0	
22	8	38	12223	1	30	0	
1	7	6	15348	1	3	0	
1	12	6	22928	1	3	0	
22	4	114	13010	1	1	0	
1	23	6	19677	1	3	0	
1	22	6	14039	1	37	0	
22	15	1	12058	1	126	0	
5	2	12	49569	1	1	0	
9	30	10	7040	1	128	0	
12	30	10	8341	1	128	0	
19	30	119	2393	1	9	0	
20	32	22	6812	1	36	0	
9	32	95	121291	1	3	0	
19	4	1	5323	1	30	0	
10	1	22	53829	1	3	0	
22	3	54	12552	1	1	0	
22	11	29	12059	1	115	0	
20	2	118	10175	1	37	0	
18	20	24	92363	1	36	0	
1	29	6	14046	1	3	0	
22	29	118	11782	1	3	0	
3	17	156	18451	1	95	0	
15	7	26	22338	1	1	0	
22	19	35	8714	1	113	0	
1	25	6	11513	1	13	0	
1	17	6	14034	1	70	0	
2	17	140	34463	1	20	0	
4	19	158	10510	1	31	0	
4	23	105	18565	1	48	0	
2	19	113	25561	1	15	0	
10	15	81	28265	1	20	0	
2	15	113	49997	1	20	0	
2	28	113	29917	1	20	0	
6	29	144	16645	1		0	
10	29	5	21875	1	3	0	
2	10	159	42823	1	69	0	
10	10	46	35358	1	2	0	
12	4	22	14089	1	1	0	
1	16	6	15375	1	18	0	
9	26	53	136836	1	3	0	
2	23	113	54987	1	3	0	
2	25	113	27004	1	13	0	
5	12	32	70377	1	1	0	
4	10	162	18542	1	33	0	
8	12	143	87940	1	3	0	
10	6	91	71348	1	4	0	
9	6	53	136592	1	4	0	
9	5	53	75809	1	3	0	
8	25	5	38878	1	13	0	
10	28	81	20977	1	20	0	
5	28	45	13923	1	95	0	
5	18	3	20681	1	1	0	
21	25	60	3820	1	77	0	
20	9	118	5050	1	117	0	
5	25	12	12609	1	13	0	
21	16	36	4408	1	131	0	
21	3	31	3849	1	68	0	
8	6	137	131634	1	4	0	
18	21	24	76319	1	1	0	
18	5	24	40670	1	1	0	
18	6	24	53404	1	4	0	
18	4	24	40669	1	1	0	
18	2	24	37360	1	1	0	
15	4	114	22076	1	1	0	
19	6	30	7802	1	4	0	
6	9	2	22533	1	3	0	
3	5	3	26816	1	94	0	
3	9	3	23657	1	56	0	
4	1	3	10749	1	72	0	
12	11	24	11613	1	52	0	
12	2	24	16274	1	1	0	
10	2	22	46067	1	36	0	
17	12	1	11246	1	30	0	
16	16	31	12884	1	19	0	
13	26	100	59728	1	3	0	
12	25	114	10877	1	13	0	
3	25	3	21213	1	13	0	
14	3	29	11901	1	30	0	
4	4	170	10569	1	72	0	
19	18	1	5163	1	44	0	
20	18	1	5083	1	51	0	
19	21	31	5892	1	37	0	
19	29	118	5078	1	37	0	
18	26	39	153852	1	3	0	
9	29	53	40595	1	15	0	
14	6	73	12189	1	4	0	
9	15	25	47335	1	57	0	
9	7	53	67147	1	3	0	
21	24	54	4095	1	127	0	
15	5	26	22398	1	1	0	
5	4	45	49157	1	1	0	
10	22	5	32456	1	1	0	
10	25	5	18629	1	13	0	
15	12	5	33321	1	1	0	
5	15	12	26378	1	20	0	
5	23	32	80584	1	1	0	
3	3	3	29264	1	55	0	
3	12	3	25249	1	56	0	
5	8	32	70444	1	1	0	
14	12	161	12449	1	30	0	
5	13	32	31657	1	20	0	
17	10	1	10771	1	42	0	
4	16	82	13530	1	149	0	
5	6	45	28992	1	4	0	
11	1	10	24084	1	1	0	
9	4	160	67152	1	3	0	
9	13	53	57569	1	57	0	
8	19	48	40044	1	15	0	
8	23	14	116686	1	3	0	
12	10	24	14884	1	2	0	
3	11	3	22730	1	14	0	
19	16	1	5200	1	18	0	
19	15	31	5219	1	132	0	
19	24	92	5737	1	11	0	
15	23	5	30331	1	1	0	
17	2	173	10722	1	1	0	
16	3	173	16116	1	1	0	
16	4	173	16118	1	1	0	
16	22	173	13394	1	1	0	
16	25	139	11539	1	13	0	
22	2	6	12568	1	1	0	
11	7	10	12892	1	36	0	
12	13	36	11597	1	90	0	
15	24	130	21707	1	30	0	
16	6	20	21155	1	4	0	
10	8	5	48805	1	3	0	
8	15	70	39253	1	57	0	
11	15	10	16325	1	122	0	
12	15	24	12266	1	122	0	
18	15	24	18660	1	110	0	
15	15	26	22223	1	102	0	
17	15	76	10770	1	65	0	
6	19	3	14063	1	31	0	
12	19	34	10466	1	31	0	
17	19	54	10679	1	31	0	
5	19	3	12512	1	31	0	
21	18	1	3665	1	68	0	
21	15	28	4370	1	107	0	
3	18	3	21769	1	56	0	
3	4	3	20546	1	30	0	
3	16	82	26865	1		0	
3	22	3	18450	1	3	0	
3	10	3	27233	1	56	0	
16	27	22	32379	1	12	0	
1	28	6	10348	1	66	0	
2	9	70	41021	1	3	0	
15	13	26	22846	1	147	0	
16	19	7	8541	1	135	0	
4	17	79	12761	1	140	0	
18	13	24	19369	1	110	0	
12	22	145	10877	1	37	0	
16	10	173	15016	1	2	0	
6	10	2	27519	1	2	0	
1	11	6	13413	1	122	0	
5	24	12	49261	1	1	0	
11	6	10	32516	1	4	0	
17	9	1	11070	1	19	0	
20	4	31	4722	1	88	0	
1	2	6	15384	1	37	0	
6	8	13	37528	1	3	0	
7	29	7	21634	1	1	0	
7	16	3	21282	1		0	
17	28	1	10556	1	150	0	
21	20	24	5610	1	37	0	
16	9	76	13490	1	1	0	
16	20	46	16698	1	36	0	
7	12	30	23884	1	1	0	
5	16	45	29116	1	18	0	
6	16	3	19186	1	19	0	
10	16	82	28043	1	19	0	
2	7	113	40575	1	3	0	
2	11	140	36077	1	20	0	
12	23	24	15769	1	1	0	
12	20	22	16271	1	1	0	
14	2	10	11892	1	36	0	
14	7	10	11697	1	36	0	
14	11	37	10526	1	154	0	
15	19	10	10722	1	68	0	
14	22	5	11719	1	1	0	
14	16	114	10496	1	19	0	
14	27	22	14665	1	12	0	
14	9	10	11851	1	1	0	
15	9	26	20698	1	148	0	
2	16	3	35162	1	19	0	
18	16	24	19590	1	18	0	
18	31	24	36024	1	36	0	
13	30	10	10578	1	128	0	
12	5	22	14072	1	1	0	
10	5	5	46218	1	3	0	
7	5	7	21708	1	1	0	
2	5	113	40239	1	3	0	
1	1	6	15372	1	30	0	
12	1	22	14583	1	1	0	
15	1	5	22223	1	1	0	
8	1	14	84589	1	3	0	
5	1	32	40467	1	1	0	
2	2	126	43720	1	3	0	
4	2	61	14404	1	37	0	
11	2	10	28436	1	37	0	
20	7	31	5081	1	31	0	
5	7	12	40280	1	1	0	
2	3	140	47344	1	28	0	
9	3	53	67147	1	30	0	
1	3	6	19017	1	2	0	
18	3	22	40665	1	4	0	
13	3	30	21567	1	1	0	
13	6	30	30807	1	4	0	
2	13	36	48169	1	20	0	
17	18	3	10818	1	34	0	
4	18	3	13259	1	87	0	
12	18	3	12184	1	1	0	
14	18	3	11849	1	1	0	
18	18	24	15309	1	1	0	
7	18	17	16225	1	157	0	
15	28	34	11164	1	139	0	
7	4	7	21704	1	3	0	
10	4	5	45086	1	3	0	
13	4	30	27654	1	1	0	
20	26	6	5085	1	3	0	
19	26	5	5899	1	3	0	
4	26	15	14410	1	37	0	
7	6	30	22912	1	4	0	
15	6	20	30298	1	4	0	
8	16	3	39363	1	19	0	
9	16	82	49860	1	19	0	
15	16	26	20699	1	18	0	
5	10	12	31665	1	3	0	
11	10	10	11567	1	3	0	
20	27	22	15662	1	12	0	
1	15	6	20538	1	20	0	
7	15	76	21596	1	66	0	
16	15	76	13534	1	107	0	
4	29	79	12380	1	98	0	
19	23	5	5794	1	50	0	
14	23	15	12292	1	30	0	
6	21	46	34104	1	36	0	
2	22	5	39385	1	30	0	
18	22	145	31382	1	1	0	
17	22	37	10712	1	1	0	
20	22	27	4739	1	37	0	
7	25	7	16247	1	13	0	
17	25	141	10615	1	13	0	
20	21	68	7815	1	49	0	
6	26	5	38384	1	3	0	
4	12	161	18572	1	33	0	
20	12	118	5082	1	47	0	
10	3	22	46073	1	1	0	
20	29	118	5059	1	47	0	
3	26	21	27619	1	3	0	
19	12	5	6385	1	2	0	
19	9	119	5715	1	1	0	
21	21	35	4638	1	37	0	
5	30	10	11283	1	9	0	
20	20	118	16794	1	1	0	
18	29	144	25590	1	1	0	
4	33	185	16853	1	52	0	
6	23	63	34075	1	30	0	
19	20	5	6388	1	1	0	
1	20	6	21399	1	3	0	
17	20	1	10865	1	34	0	
4	15	58	14382	1		0	
6	25	3	12673	1	13	0	
5	29	122	31676	1	3	0	
5	31	12	40282	1	36	0	
5	9	45	28990	1	3	0	
6	6	144	44801	1	4	0	
19	7	30	5720	1	1	0	
14	1	29	11888	1	1	0	
16	18	3	12841	1	1	0	
1	5	6	17518	1	3	0	
18	33	24	20695	1	92	0	
10	7	46	37878	1	3	0	
13	20	30	22079	1	1	0	
15	22	26	20662	1	1	0	
16	28	34	11482	1	48	0	
12	29	186	12240	1	3	0	
5	22	45	17306	1	1	0	
17	23	1	10897	1	34	0	
15	14	5	30331	1	1	0	
1	18	3	12735	1	37	0	
11	23	10	24086	1	30	0	
15	21	5	30332	1	36	0	
17	13	69	10807	1		0	
22	9	36	12074	1	3	0	
19	13	35	5148	1	136	0	
2	33	113	46865	1	92	0	
14	33	34	11698	1	115	0	
21	12	24	4668	1	2	0	
21	23	24	4421	1	127	0	
22	22	24	12063	1	3	0	
18	14	24	35002	1	1	0	
15	29	10	20699	1	1	0	
3	7	82	23012	1	153	0	
14	10	24	11890	1	2	0	
22	32	24	12568	1	36	0	
22	1	114	12711	1	1	0	
2	29	186	34538	1	3	0	
17	26	1	10804	1	97	0	
22	24	64	12456	1	1	0	
11	29	10	11121	1	37	0	
20	11	60	4740	1	121	0	
20	17	118	5052	1	74	0	
18	28	125	12741	1	66	0	
20	33	22	5971	1	93	0	
3	30	10	11423	1	9	0	
11	30	10	7260	1	128	0	
20	24	118	5050	1	31	0	
8	9	14	63236	1	3	0	
3	21	82	28740	1	3	0	
10	9	46	35933	1	3	0	
22	5	126	12423	1	3	0	
16	33	154	13533	1		0	
9	33	160	52271	1	43	0	
14	29	10	10501	1	1	0	
9	20	160	95789	1	3	0	
11	14	24	20777	1	3	0	
17	17	79	10645	1	101	0	
5	21	12	69239	1	1	0	
4	11	191	12333	1	95	0	
11	17	10	11119	1	20	0	
16	13	69	13534	1	20	0	
8	2	5	84345	1	3	0	
11	33	10	16323	1	111	0	
11	8	10	23113	1	30	0	
13	17	38	15688	1	66	0	
3	20	82	27978	1	3	0	
8	5	5	87950	1	3	0	
14	8	10	11895	1	30	0	
3	1	196	22895	1	30	0	Achieved on the Chinese Version of HCR2 ð
13	10	38	15943	1	2	0	
8	14	14	87945	1	3	0	
13	14	38	20304	1	1	0	
9	28	160	21971	1	45	0	
18	25	145	13461	1	13	0	
17	11	16	10816	1	120	0	
19	17	118	5068	1	73	0	
1	27	142	51975	1	12	0	
7	28	190	12281	1	145	0	
6	28	199	13145	1		0	
22	10	12	12563	1	1	0	
12	9	157	12191	1	36	0	
13	11	38	15436	1	6	0	
13	15	38	15543	1	66	0	
21	1	29	4074	1	37	0	
13	28	38	11799	1	66	0	
6	27	200	93683	1	12	0	
2	26	5	98184	1	3	0	
13	16	38	15685	1	19	0	
4	3	201	16199	1	11	0	
19	27	10	19259	1	12	0	
13	19	38	11799	1	31	0	
9	23	95	67155	1	30	0	
15	27	43	71358	1	12	0	
1	26	6	20542	1	3	0	
15	33	26	22080	1	143	0	
17	1	29	10681	1	1	0	
5	27	24	87402	1	12	0	
13	33	38	15683	1	29	0	
9	1	160	70003	1	30	0	
20	15	118	5051	1	7	0	
3	8	13	22572	1	30	0	
13	31	38	20732	1	1	0	
13	29	38	16184	1	1	0	
13	25	38	15952	1	39	0	
22	6	203	13281	1	4	0	
1	10	6	17405	1	42	0	
1	31	6	20561	1	3	0	
2	31	113	49183	1	3	0	
20	31	118	5066	1	38	0	
10	23	5	45087	1	3	0	
19	22	209	5082	1	37	0	
10	27	10	220897	1	58	0	
9	27	53	136595	1	35	0	
15	31	5	30333	1	1	0	
2	14	24	51102	1	3	0	
13	18	38	15931	1	1	0	
7	20	7	45579	1	3	0	
8	20	5	140740	1	36	0	
8	21	5	106938	1	36	0	
1	8	6	15362	1	30	0	
21	9	213	4095	1	75	0	
6	1	29	35011	1	1	0	
21	31	24	4730	1	37	0	
8	31	5	125818	1	3	0	
11	28	10	9338	1	82	0	
11	4	10	23082	1	83	0	
19	31	5	5825	1	1	0	
14	21	29	12441	1	30	0	
15	20	5	35988	1	36	0	
3	27	188	70477	1	12	0	
13	9	38	16388	1	1	0	
13	7	38	16716	1	1	0	
21	27	22	6087	1	12	0	
19	5	53	5720	1	2	0	
22	28	114	11113	1	87	0	
19	3	114	5349	1	88	0	
17	31	24	10735	1	35	0	
12	33	24	14798	1	52	0	
13	22	38	17951	1	1	0	
13	23	38	19323	1	1	0	
13	24	38	20732	1	1	0	
22	21	126	12737	1	1	0	
19	11	84	5008	1	75	0	
8	29	120	41436	1	3	0	
11	27	10	71586	1	12	0	
17	7	24	10733	1	79	0	
12	31	24	14852	1	1	0	
7	27	35	100200	1	58	0	
1	19	7	10610	1	15	0	
8	27	132	319752	1	12	0	
6	15	134	27607	1	20	1	
16	30	215	6475	1	46	0	
22	18	38	12009	1	1	0	
22	14	38	12567	1	1	0	
11	16	10	10489	1	18	0	
17	29	1	10670	1	99	0	
14	20	15	12400	1	100	0	
4	28	10	12302	1	87	0	
22	13	12	12091	1	101	0	
1	14	6	24657	1	3	0	
15	18	36	14636	1	1	0	
17	4	24	10657	1	1	0	
22	27	203	16585	1	12	0	
12	27	10	25162	1	103	0	
4	30	29	10492	1	9	0	
4	20	162	18528	1	48	0	
20	25	6	4746	1	77	0	
4	22	24	12325	1	48	0	
9	8	53	95761	1	3	0	
9	25	53	26169	1	35	0	
9	31	53	67163	1	30	0	
21	4	10	3667	1	113	0	
18	8	83	40663	1	3	0	
6	22	2	17925	1	3	0	
6	3	2	34070	1	30	0	
17	5	1	10845	1	40	0	
12	12	157	16898	1	30	0	
18	9	5	23991	1	1	0	
8	22	14	52751	1	3	0	
14	4	24	11878	1	1	0	
2	32	218	41576	1	36	0	
6	18	3	15260	1		0	
7	23	7	46438	1	1	0	
22	7	180	12563	1	1	0	
14	25	10	10494	1	13	0	
21	10	60	4513	1	11	0	
2	24	203	62343	1	3	0	
14	19	114	10346	1	47	0	
4	6	38	12195	1	4	0	
9	10	3	47329	1	2	0	
9	18	3	28242	1	47	0	
18	17	1	13429	1	66	0	
20	6	118	5057	1	4	0	
11	25	10	11112	1	13	0	
8	10	1	48492	1	1	0	
17	32	219	12988	1	3	0	
2	21	113	60111	1	36	0	
1	30	29	8639	1	46	0	
17	30	29	7446	1	46	0	
10	30	29	8220	1	46	0	
16	5	17	16067	1	1	0	
5	14	122	49130	1	1	0	
21	14	122	3849	1	81	0	
17	27	203	14966	1	152	0	
4	32	142	18559	1	123	0	
16	29	186	12721	1	1	0	
14	30	29	8399	1	46	0	
19	19	48	4161	1	156	0	
3	15	222	27213	1	95	0	Achieved on the Chinese Version of HCR2 ð
1	32	142	23803	1	3	0	
3	32	222	18383	1	36	0	Achieved on the Chinese Version of HCR2 ð
3	14	222	22910	1	105	0	Achieved on the Chinese Version of HCR2 ð
11	11	10	10509	1	33	0	
20	10	118	8667	1	11	0	
11	3	10	24071	1	30	0	
11	5	10	23147	1	3	0	
21	7	24	4676	1	160	0	
2	20	24	85311	1	3	0	
12	7	5	14118	1	1	0	
6	2	5	30795	1	37	0	
6	7	5	26844	1	3	0	
16	31	5	16044	1	1	0	
16	21	5	16171	1	1	0	
16	23	5	16112	1	1	0	
16	7	5	16108	1	1	0	
16	14	5	16109	1	1	0	
6	4	5	30793	1	37	0	
6	31	5	37533	1	3	0	
6	14	5	34105	1	3	0	
10	31	5	46220	1	1	0	
2	4	5	41026	1	1	0	
12	14	24	17022	1	2	0	
3	33	226	27213	1	161	0	
19	32	201	6019	1	3	0	
12	21	24	16268	1	3	0	
11	9	10	16158	1	3	0	
7	32	127	15087	1	36	0	
15	17	235	18010	1	20	0	
9	34	53	95791	1	36	0	
19	33	77	6504	1	7	0	
17	33	237	11036	1	164	0	
20	16	118	5060	1	165	0	
22	23	47	12710	1	1	0	
5	33	122	31650	1	166	0	
11	22	10	15406	1	1	0	
2	34	113	73374	1	36	0	
19	34	53	5718	1	36	0	
6	30	29	8815	1	128	0	
22	16	10	12060	1	18	0	
15	34	53	30364	1	36	0	
17	21	1	10808	1	109	0	
2	27	35	222222	1	12	0	
1	34	6	20549	1	36	0	
16	32	237	14432	1	36	0	
8	28	244	16615	1	66	0	
22	34	180	13224	1	36	0	
21	22	27	3700	1	169	0	
21	34	24	4073	1	167	0	
10	33	245	34852	1	20	0	
4	34	191	16236	1	171	0	
7	34	7	48119	1	36	0	
10	34	22	98261	1	36	0	
6	34	24	40155	1	36	0	
16	34	24	16735	1	36	0	
14	34	24	11899	1	36	0	
21	33	24	5738	1	75	0	
15	25	10	11160	1	13	0	
6	32	22	19186	1	36	0	
9	14	24	86662	1	3	0	
14	32	134	12128	1	3	1	
5	34	122	70293	1	36	0	
14	28	10	10446	1	66	0	
22	20	203	13221	1	36	0	
3	23	82	25922	1	94	0	
20	23	185	5942	1	129	0	
11	20	10	35529	1	3	0	
6	12	46	36708	1	3	0	
17	34	1	10675	1	173	0	
6	33	247	27524	1	20	0	
8	33	247	39739	1	122	0	
14	31	7	12450	1	1	0	
9	21	53	85749	1	1	0	
8	34	53	144724	1	36	0	
22	33	249	12132	1	66	0	
10	14	185	45092	1	3	0	
7	14	120	21708	1	1	0	
5	32	122	16391	1	1	0	
20	8	18	3921	1	174	0	
3	28	3	20331	1	150	0	
2	30	29	21061	1	46	0	
11	31	10	29363	1	3	0	
11	21	10	29435	1	3	0	
22	26	47	18298	1	3	0	
3	31	188	22087	1	135	0	
14	14	29	12407	1	30	0	
4	14	185	14588	1	33	0	
20	14	118	5082	1	7	0	
16	12	5	16121	1	1	0	
3	34	212	38051	1	36	0	
13	21	38	20732	1	1	0	
22	25	10	12063	1	13	0	
4	7	105	16233	1	33	0	
22	12	12	12564	1	1	0	
14	15	10	11849	1	7	0	
21	32	119	5394	1	123	0	
5	26	32	134826	1	3	0	
12	28	118	10384	1	48	0	
11	19	10	10392	1	31	0	
11	26	46	23085	1	3	0	
12	26	22	16881	1	36	0	
8	30	6	10876	1	128	0	
19	25	84	4238	1	13	0	
17	14	185	10885	1	34	0	
11	18	10	11155	1	49	0	
18	27	250	111119	1	12	0	Achieved on the Chinese Version of HCR2 ð
2	18	251	18848	1		0	Achieved on the Chinese Version of HCR2 ð
9	12	223	85762	1	1	0	Achieved on the Chinese Version of HCR2 ð
10	20	223	57923	1	3	0	Achieved on the Chinese Version of HCR2 ð
13	5	38	20742	1	1	0	
22	31	180	12738	1	1	0	
19	14	7	5322	1	38	0	
1	33	142	25598	1	33	0	
12	34	22	16954	1	36	0	
13	8	38	21072	1	1	0	
4	25	105	12363	1	175	0	
18	34	22	77679	1	36	0	
7	33	122	21598	1	66	0	
9	22	53	53362	1	3	0	
13	34	38	23873	1	36	0	
4	31	185	18039	1	3	0	
4	21	185	16637	1	22	0	
4	27	185	12382	1	35	0	
4	13	185	14256	1	48	0	
10	21	223	45050	1	3	0	Achieved on the Chinese Version of HCR2 ð
4	9	105	15765	1	42	0	
20	34	118	5058	1	170	0	
15	10	12	22953	1		0	
11	34	10	32432	1	36	0	
\.


--
-- PostgreSQL database dump complete
--

