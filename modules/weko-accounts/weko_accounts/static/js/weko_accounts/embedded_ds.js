// To use this JavaScript, please access:
// https://ds.gakunin.nii.ac.jp/WAYF/embedded-wayf.js/snippet.html?1583392121839
// and copy/paste the resulting HTML snippet to an unprotected web page that
// you want the LANGUAGES to be displayed

// ############################################################################

// Declare all variables
var wayf_use_discovery_service;
var wayf_use_small_logo = true;
var wayf_width;
var wayf_height;
var wayf_background_color = '#fff';
var wayf_border_color;
var wayf_font_color;
var wayf_font_size;
var wayf_hide_logo;
var wayf_auto_login;
var wayf_logged_in_messsage;
var wayf_hide_after_login;
var wayf_most_used_idps;
var wayf_show_categories;
var wayf_hide_categories;
var wayf_hide_idps;
var wayf_unhide_idps;
var wayf_show_remember_checkbox;
var wayf_force_remember_for_session;
var wayf_additional_idps = [
    {
        "entityID": "https://core.orthros.gakunin.nii.ac.jp/idp",
        "name": "Orthros",
        "search": ["https://core.orthros.gakunin.nii.ac.jp/idp", "Orthros"]
    },
];
var wayf_discofeed_url;
var wayf_sp_cookie_path;
var wayf_list_height;
var wayf_sp_samlDSURL;
var wayf_sp_samlACURL;
var wayf_html = "";

var wayf_idps = {
    "https://shib-idp01.iic.hokudai.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "Hokkaido University",
        search: ["https://shib-idp01.iic.hokudai.ac.jp/idp/shibboleth", "Hokkaido", "Hokkaido University", "Hokkaido University", "北海道大学"],
        SAML1SSOurl: "https://shib-idp01.iic.hokudai.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.asahikawa-med.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "Asahikawa Medical University",
        search: ["https://idp.asahikawa-med.ac.jp/idp/shibboleth", "Hokkaido", "Asahikawa Medical University", "Asahikawa Medical University", "旭川医科大学"],
        SAML1SSOurl: "https://idp.asahikawa-med.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.msls.kushiro-ct.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "National Institute of Technology,Kushiro College",
        search: ["https://idp.msls.kushiro-ct.ac.jp/idp/shibboleth", "Hokkaido", "National Institute of Technology,Kushiro College", "National Institute of Technology,Kushiro College", "釧路工業高等専門学校"],
        SAML1SSOurl: "https://idp.msls.kushiro-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shibboleth.lib.kitami-it.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "Kitami Institute of Technology",
        search: ["https://shibboleth.lib.kitami-it.ac.jp/idp/shibboleth", "Hokkaido", "Kitami Institute of Technology", "Kitami Institute of Technology", "北見工業大学"],
        SAML1SSOurl: "https://shibboleth.lib.kitami-it.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://sso.sapmed.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "Sapporo Medical University",
        search: ["https://sso.sapmed.ac.jp/idp/shibboleth", "Hokkaido", "Sapporo Medical University", "Sapporo Medical University", "札幌医科大学"],
        SAML1SSOurl: "https://sso.sapmed.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.tomakomai-ct.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "National Institute of Technology,Tomakomai College",
        search: ["https://kidp.tomakomai-ct.ac.jp/idp/shibboleth", "Hokkaido", "National Institute of Technology,Tomakomai College", "National Institute of Technology,Tomakomai College", "苫小牧工業高等専門学校"],
        SAML1SSOurl: "https://kidp.tomakomai-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.hakodate-ct.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "National Institute of Technology,Hakodate College",
        search: ["https://kidp.hakodate-ct.ac.jp/idp/shibboleth", "Hokkaido", "National Institute of Technology,Hakodate College", "National Institute of Technology,Hakodate College", "函館工業高等専門学校"],
        SAML1SSOurl: "https://kidp.hakodate-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.asahikawa-nct.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "National Institute of Technology,Asahikawa College",
        search: ["https://kidp.asahikawa-nct.ac.jp/idp/shibboleth", "Hokkaido", "National Institute of Technology,Asahikawa College", "National Institute of Technology,Asahikawa College", "旭川工業高等専門学校"],
        SAML1SSOurl: "https://kidp.asahikawa-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.sgu.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "Sapporo Gakuin University",
        search: ["https://idp.sgu.ac.jp/idp/shibboleth", "Hokkaido", "Sapporo Gakuin University", "Sapporo Gakuin University", "札幌学院大学"],
        SAML1SSOurl: "https://idp.sgu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin-idp01.mmm.muroran-it.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "Muroran Institute of Technology",
        search: ["https://gakunin-idp01.mmm.muroran-it.ac.jp/idp/shibboleth", "Hokkaido", "Muroran Institute of Technology", "Muroran Institute of Technology", "室蘭工業大学"],
        SAML1SSOurl: "https://gakunin-idp01.mmm.muroran-it.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.fun.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "Future University Hakodate",
        search: ["https://idp.fun.ac.jp/idp/shibboleth", "Hokkaido", "Future University Hakodate", "Future University Hakodate", "公立はこだて未来大学"],
        SAML1SSOurl: "https://idp.fun.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.hokkyodai.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "Hokkaido University of Education",
        search: ["https://idp.hokkyodai.ac.jp/idp/shibboleth", "Hokkaido", "Hokkaido University of Education", "Hokkaido University of Education", "北海道教育大学"],
        SAML1SSOurl: "https://idp.hokkyodai.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://sib-idp.obihiro.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "Obihiro University of Agriculture and Veterinary Medicine",
        search: ["https://sib-idp.obihiro.ac.jp/idp/shibboleth", "Hokkaido", "Obihiro University of Agriculture and Veterinary Medicine", "Obihiro University of Agriculture and Veterinary Medicine", "帯広畜産大学"],
        SAML1SSOurl: "https://sib-idp.obihiro.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.scu.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "Sapporo City University",
        search: ["https://idp.scu.ac.jp/idp/shibboleth", "Hokkaido", "Sapporo City University", "Sapporo City University", "札幌市立大学"],
        SAML1SSOurl: "https://idp.scu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://rg-lshib01.rakuno.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "RAKUNO GAKUEN UNIVERSITY",
        search: ["https://rg-lshib01.rakuno.ac.jp/idp/shibboleth", "Hokkaido", "RAKUNO GAKUEN UNIVERSITY", "RAKUNO GAKUEN UNIVERSITY", "酪農学園大学"],
        SAML1SSOurl: "https://rg-lshib01.rakuno.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://ictc-idp01.otaru-uc.ac.jp/idp/shibboleth": {
        type: "hokkaido",
        name: "Otaru University of Commerce",
        search: ["https://ictc-idp01.otaru-uc.ac.jp/idp/shibboleth", "Hokkaido", "Otaru University of Commerce", "Otaru University of Commerce", "⼩樽商科⼤学"],
        SAML1SSOurl: "https://ictc-idp01.otaru-uc.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://upki.yamagata-u.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "Yamagata University",
        search: ["https://upki.yamagata-u.ac.jp/idp/shibboleth", "Tohoku", "Yamagata University", "Yamagata University", "山形大学"],
        SAML1SSOurl: "https://upki.yamagata-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.miyakyo-u.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "Miyagi University of Education",
        search: ["https://idp.miyakyo-u.ac.jp/idp/shibboleth", "Tohoku", "Miyagi University of Education", "Miyagi University of Education", "宮城教育大学"],
        SAML1SSOurl: "https://no.saml1.sso.url.defined.com/error"
    },
    "https://kidp.ichinoseki.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "National Institute of Technology,Ichinoseki College",
        search: ["https://kidp.ichinoseki.ac.jp/idp/shibboleth", "Tohoku", "National Institute of Technology,Ichinoseki College", "National Institute of Technology,Ichinoseki College", "一関工業高等専門学校"],
        SAML1SSOurl: "https://kidp.ichinoseki.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.hachinohe-ct.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "National Institute of Technology,Hachinohe College",
        search: ["https://kidp.hachinohe-ct.ac.jp/idp/shibboleth", "Tohoku", "National Institute of Technology,Hachinohe College", "National Institute of Technology,Hachinohe College", "八戸工業高等専門学校"],
        SAML1SSOurl: "https://kidp.hachinohe-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://ksidp.sendai-nct.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "National Institute of Technology,Sendai College,Hirose",
        search: ["https://ksidp.sendai-nct.ac.jp/idp/shibboleth", "Tohoku", "National Institute of Technology,Sendai College,Hirose", "National Institute of Technology,Sendai College,Hirose", "仙台高等専門学校　広瀬キャンパス"],
        SAML1SSOurl: "https://ksidp.sendai-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.akita-nct.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "National Institute of Technology,Akita College",
        search: ["https://kidp.akita-nct.ac.jp/idp/shibboleth", "Tohoku", "National Institute of Technology,Akita College", "National Institute of Technology,Akita College", "秋田工業高等専門学校"],
        SAML1SSOurl: "https://kidp.akita-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.auth.tohoku.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "Tohoku University",
        search: ["https://idp.auth.tohoku.ac.jp/idp/shibboleth", "Tohoku", "Tohoku University", "Tohoku University", "東北大学"],
        SAML1SSOurl: "https://idp.auth.tohoku.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.tsuruoka-nct.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "National Institute of Technology,Tsuruoka College",
        search: ["https://kidp.tsuruoka-nct.ac.jp/idp/shibboleth", "Tohoku", "National Institute of Technology,Tsuruoka College", "National Institute of Technology,Tsuruoka College", "鶴岡工業高等専門学校"],
        SAML1SSOurl: "https://kidp.tsuruoka-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.fukushima-nct.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "National Institute of Technology,Fukushima College",
        search: ["https://kidp.fukushima-nct.ac.jp/idp/shibboleth", "Tohoku", "National Institute of Technology,Fukushima College", "National Institute of Technology,Fukushima College", "福島工業高等専門学校"],
        SAML1SSOurl: "https://kidp.fukushima-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://knidp.sendai-nct.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "National Institute of Technology,Sendai College,Natori",
        search: ["https://knidp.sendai-nct.ac.jp/idp/shibboleth", "Tohoku", "National Institute of Technology,Sendai College,Natori", "National Institute of Technology,Sendai College,Natori", "仙台高等専門学校 名取キャンパス"],
        SAML1SSOurl: "https://knidp.sendai-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.tohtech.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "Tohoku Institute of Technology",
        search: ["https://idp.tohtech.ac.jp/idp/shibboleth", "Tohoku", "Tohoku Institute of Technology", "Tohoku Institute of Technology", "東北工業大学"],
        SAML1SSOurl: "https://idp.tohtech.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://auas.akita-u.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "Akita University",
        search: ["https://auas.akita-u.ac.jp/idp/shibboleth", "Tohoku", "Akita University", "Akita University", "秋田大学"],
        SAML1SSOurl: "https://auas.akita-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp01.gn.hirosaki-u.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "Hirosaki University",
        search: ["https://idp01.gn.hirosaki-u.ac.jp/idp/shibboleth", "Tohoku", "Hirosaki University", "Hirosaki University", "弘前大学"],
        SAML1SSOurl: "https://idp01.gn.hirosaki-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.u-aizu.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "The University of Aizu",
        search: ["https://idp.u-aizu.ac.jp/idp/shibboleth", "Tohoku", "The University of Aizu", "The University of Aizu", "会津大学"],
        SAML1SSOurl: "https://idp.u-aizu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://axl.aiu.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "Akita International University",
        search: ["https://axl.aiu.ac.jp/idp/shibboleth", "Tohoku", "Akita International University", "Akita International University", "国際教養大学"],
        SAML1SSOurl: "https://axl.aiu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.fmu.ac.jp/idp/shibboleth": {
        type: "tohoku",
        name: "Fukushima Medical University",
        search: ["https://idp.fmu.ac.jp/idp/shibboleth", "Tohoku", "Fukushima Medical University", "Fukushima Medical University", "福島県立医科大学"],
        SAML1SSOurl: "https://idp.fmu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://tg.ex-tic.com/auth/gakunin/saml2/assertions": {
        type: "tohoku",
        name: "Tohoku Gakuin University",
        search: ["https://tg.ex-tic.com/auth/gakunin/saml2/assertions", "Tohoku", "Tohoku Gakuin University", "Tohoku Gakuin University", "東北学院大学"],
        SAML1SSOurl: "https://no.saml1.sso.url.defined.com/error"
    },
    "https://idp.nii.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "National Institute of Informatics",
        search: ["https://idp.nii.ac.jp/idp/shibboleth", "Kanto", "National Institute of Informatics", "National Institute of Informatics", "国立情報学研究所"],
        SAML1SSOurl: "https://idp.nii.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://upki-idp.chiba-u.jp/idp/shibboleth": {
        type: "kanto",
        name: "Chiba University",
        search: ["https://upki-idp.chiba-u.jp/idp/shibboleth", "Kanto", "Chiba University", "Chiba University", "千葉大学"],
        SAML1SSOurl: "https://upki-idp.chiba-u.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.account.tsukuba.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "University of Tsukuba",
        search: ["https://idp.account.tsukuba.ac.jp/idp/shibboleth", "Kanto", "University of Tsukuba", "University of Tsukuba", "筑波大学"],
        SAML1SSOurl: "https://idp.account.tsukuba.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://asura.seijo.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Seijo University",
        search: ["https://asura.seijo.ac.jp/idp/shibboleth", "Kanto", "Seijo University", "Seijo University", "成城大学"],
        SAML1SSOurl: "https://asura.seijo.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://upki.toho-u.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Toho University",
        search: ["https://upki.toho-u.ac.jp/idp/shibboleth", "Kanto", "Toho University", "Toho University", "東邦大学"],
        SAML1SSOurl: "https://upki.toho-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shibboleth.nihon-u.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Nihon University",
        search: ["https://shibboleth.nihon-u.ac.jp/idp/shibboleth", "Kanto", "Nihon University", "Nihon University", "日本大学"],
        SAML1SSOurl: "https://shibboleth.nihon-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://upki-idp.rikkyo.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Rikkyo University",
        search: ["https://upki-idp.rikkyo.ac.jp/idp/shibboleth", "Kanto", "Rikkyo University", "Rikkyo University", "立教大学"],
        SAML1SSOurl: "https://upki-idp.rikkyo.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://servs.lib.meiji.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Meiji University",
        search: ["https://servs.lib.meiji.ac.jp/idp/shibboleth", "Kanto", "Meiji University", "Meiji University", "明治大学"],
        SAML1SSOurl: "https://servs.lib.meiji.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://ws1.jichi.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Jichi Medical University(old)",
        search: ["https://ws1.jichi.ac.jp/idp/shibboleth", "Kanto", "Jichi Medical University(old)", "Jichi Medical University(old)", "自治医科大学(旧)"],
        SAML1SSOurl: "https://ws1.jichi.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin-idp.ynu.ac.jp/": {
        type: "kanto",
        name: "Yokohama National University",
        search: ["https://gakunin-idp.ynu.ac.jp/", "Kanto", "Yokohama National University", "Yokohama National University", "横浜国立大学"],
        SAML1SSOurl: "https://gakunin-idp.ynu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://saml-2.tmd.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo Medical and Dental University",
        search: ["https://saml-2.tmd.ac.jp/idp/shibboleth", "Kanto", "Tokyo Medical and Dental University", "Tokyo Medical and Dental University", "東京医科歯科大学"],
        SAML1SSOurl: "https://saml-2.tmd.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.kosen-k.go.jp/idp/shibboleth": {
        type: "kanto",
        name: "National Institute of Technology",
        search: ["https://kidp.kosen-k.go.jp/idp/shibboleth", "Kanto", "National Institute of Technology", "National Institute of Technology", "国立高等専門学校機構"],
        SAML1SSOurl: "https://kidp.kosen-k.go.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.tdc.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo Dental College",
        search: ["https://idp.tdc.ac.jp/idp/shibboleth", "Kanto", "Tokyo Dental College", "Tokyo Dental College", "東京歯科大学"],
        SAML1SSOurl: "https://idp.tdc.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shib.ap.showa-u.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Showa University",
        search: ["https://shib.ap.showa-u.ac.jp/idp/shibboleth", "Kanto", "Showa University", "Showa University", "昭和大学"],
        SAML1SSOurl: "https://shib.ap.showa-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://ill.lib.kth.isp.ntt-east.co.jp/idp/shibboleth": {
        type: "kanto",
        name: "NTT Medical Center Tokyo",
        search: ["https://ill.lib.kth.isp.ntt-east.co.jp/idp/shibboleth", "Kanto", "NTT Medical Center Tokyo", "NTT Medical Center Tokyo", "NTT東日本関東病院"],
        SAML1SSOurl: "https://ill.lib.kth.isp.ntt-east.co.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp01.ipc.kaiyodai.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo University of Marine Science and Technology",
        search: ["https://idp01.ipc.kaiyodai.ac.jp/idp/shibboleth", "Kanto", "Tokyo University of Marine Science and Technology", "Tokyo University of Marine Science and Technology", "東京海洋大学"],
        SAML1SSOurl: "https://idp01.ipc.kaiyodai.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.soka.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Soka University",
        search: ["https://idp.soka.ac.jp/idp/shibboleth", "Kanto", "Soka University", "Soka University", "創価大学"],
        SAML1SSOurl: "https://idp.soka.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.igakuken.or.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo Metropolitan Institute of Medical Science",
        search: ["https://idp.igakuken.or.jp/idp/shibboleth", "Kanto", "Tokyo Metropolitan Institute of Medical Science", "Tokyo Metropolitan Institute of Medical Science", "東京都医学総合研究所"],
        SAML1SSOurl: "https://idp.igakuken.or.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakuninidp.sic.shibaura-it.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Shibaura Institute of Technology",
        search: ["https://gakuninidp.sic.shibaura-it.ac.jp/idp/shibboleth", "Kanto", "Shibaura Institute of Technology", "Shibaura Institute of Technology", "芝浦工業大学"],
        SAML1SSOurl: "https://gakuninidp.sic.shibaura-it.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://tgu.u-gakugei.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo Gakugei University",
        search: ["https://tgu.u-gakugei.ac.jp/idp/shibboleth", "Kanto", "Tokyo Gakugei University", "Tokyo Gakugei University", "東京学芸大学"],
        SAML1SSOurl: "https://no.saml1.sso.url.defined.com/error"
    },
    "https://idp.musashi.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Musashi Academy",
        search: ["https://idp.musashi.ac.jp/idp/shibboleth", "Kanto", "Musashi Academy", "Musashi Academy", "武蔵学園"],
        SAML1SSOurl: "https://idp.musashi.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.it-chiba.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Chiba Institute of Technology",
        search: ["https://idp.it-chiba.ac.jp/idp/shibboleth", "Kanto", "Chiba Institute of Technology", "Chiba Institute of Technology", "千葉工業大学"],
        SAML1SSOurl: "https://idp.it-chiba.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shibboleth.tama.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tama University",
        search: ["https://shibboleth.tama.ac.jp/idp/shibboleth", "Kanto", "Tama University", "Tama University", "多摩大学"],
        SAML1SSOurl: "https://shibboleth.tama.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://upkishib.cc.ocha.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Ochanomizu University",
        search: ["https://upkishib.cc.ocha.ac.jp/idp/shibboleth", "Kanto", "Ochanomizu University", "Ochanomizu University", "お茶の水女子大学"],
        SAML1SSOurl: "https://upkishib.cc.ocha.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.tokyo-ct.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "National Institute of Technology,Tokyo College",
        search: ["https://kidp.tokyo-ct.ac.jp/idp/shibboleth", "Kanto", "National Institute of Technology,Tokyo College", "National Institute of Technology,Tokyo College", "東京工業高等専門学校"],
        SAML1SSOurl: "https://kidp.tokyo-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.gunma-u.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Gunma University",
        search: ["https://idp.gunma-u.ac.jp/idp/shibboleth", "Kanto", "Gunma University", "Gunma University", "群馬大学"],
        SAML1SSOurl: "https://idp.gunma-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.oyama-ct.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "National Institute of Technology,Oyama College",
        search: ["https://kidp.oyama-ct.ac.jp/idp/shibboleth", "Kanto", "National Institute of Technology,Oyama College", "National Institute of Technology,Oyama College", "小山工業高等専門学校"],
        SAML1SSOurl: "https://kidp.oyama-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin1.keio.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Keio University",
        search: ["https://gakunin1.keio.ac.jp/idp/shibboleth", "Kanto", "Keio University", "Keio University", "慶應義塾大学"],
        SAML1SSOurl: "https://gakunin1.keio.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.gunma-ct.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "National Institute of Technology,Gunma College",
        search: ["https://kidp.gunma-ct.ac.jp/idp/shibboleth", "Kanto", "National Institute of Technology,Gunma College", "National Institute of Technology,Gunma College", "群馬工業高等専門学校"],
        SAML1SSOurl: "https://kidp.gunma-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shibboleth-idp.dokkyomed.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Dokkyo Medical University",
        search: ["https://shibboleth-idp.dokkyomed.ac.jp/idp/shibboleth", "Kanto", "Dokkyo Medical University", "Dokkyo Medical University", "獨協医科大学"],
        SAML1SSOurl: "https://shibboleth-idp.dokkyomed.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://iccoam.tufs.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo University of Foreign Studies",
        search: ["https://iccoam.tufs.ac.jp/idp/shibboleth", "Kanto", "Tokyo University of Foreign Studies", "Tokyo University of Foreign Studies", "東京外国語大学"],
        SAML1SSOurl: "https://iccoam.tufs.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.ibaraki-ct.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "National Institute of Technology,Ibaraki College",
        search: ["https://kidp.ibaraki-ct.ac.jp/idp/shibboleth", "Kanto", "National Institute of Technology,Ibaraki College", "National Institute of Technology,Ibaraki College", "茨城工業高等専門学校"],
        SAML1SSOurl: "https://kidp.ibaraki-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shibboleth.cc.uec.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "The University of Electro-Communications",
        search: ["https://shibboleth.cc.uec.ac.jp/idp/shibboleth", "Kanto", "The University of Electro-Communications", "The University of Electro-Communications", "電気通信大学"],
        SAML1SSOurl: "https://shibboleth.cc.uec.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.sys.affrc.go.jp/idp/shibboleth": {
        type: "kanto",
        name: "AFFRIT/MAFFIN",
        search: ["https://idp.sys.affrc.go.jp/idp/shibboleth", "Kanto", "AFFRIT/MAFFIN", "AFFRIT/MAFFIN", "AFFRIT/MAFFIN"],
        SAML1SSOurl: "https://idp.sys.affrc.go.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.kisarazu.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "National Institute of Technology,Kisarazu College",
        search: ["https://kidp.kisarazu.ac.jp/idp/shibboleth", "Kanto", "National Institute of Technology,Kisarazu College", "National Institute of Technology,Kisarazu College", "木更津工業高等専門学校"],
        SAML1SSOurl: "https://kidp.kisarazu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin-idp.c.chuo-u.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Chuo University",
        search: ["https://gakunin-idp.c.chuo-u.ac.jp/idp/shibboleth", "Kanto", "Chuo University", "Chuo University", "中央大学"],
        SAML1SSOurl: "https://no.saml1.sso.url.defined.com/error"
    },
    "https://gidp.adm.u-tokyo.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "The University of Tokyo",
        search: ["https://gidp.adm.u-tokyo.ac.jp/idp/shibboleth", "Kanto", "The University of Tokyo", "The University of Tokyo", "東京大学"],
        SAML1SSOurl: "https://gidp.adm.u-tokyo.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.dendai.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo Denki University",
        search: ["https://idp.dendai.ac.jp/idp/shibboleth", "Kanto", "Tokyo Denki University", "Tokyo Denki University", "東京電機大学"],
        SAML1SSOurl: "https://idp.dendai.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.cc.seikei.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Seikei University",
        search: ["https://idp.cc.seikei.ac.jp/idp/shibboleth", "Kanto", "Seikei University", "Seikei University", "成蹊大学"],
        SAML1SSOurl: "https://idp.cc.seikei.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.teikyo-u.ac.jp/AccessManager/shibboleth": {
        type: "kanto",
        name: "Teikyo University",
        search: ["https://idp.teikyo-u.ac.jp/AccessManager/shibboleth", "Kanto", "Teikyo University", "Teikyo University", "帝京大学"],
        SAML1SSOurl: "https://idp.teikyo-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.tau.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo Ariake University of Medical and Health Sciences",
        search: ["https://idp.tau.ac.jp/idp/shibboleth", "Kanto", "Tokyo Ariake University of Medical and Health Sciences", "Tokyo Ariake University of Medical and Health Sciences", "東京有明医療大学"],
        SAML1SSOurl: "https://idp.tau.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.tokyo-kasei.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo Kasei University",
        search: ["https://idp.tokyo-kasei.ac.jp/idp/shibboleth", "Kanto", "Tokyo Kasei University", "Tokyo Kasei University", "東京家政大学"],
        SAML1SSOurl: "https://idp.tokyo-kasei.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.grips.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "National Graduate Institute for Policy Studies",
        search: ["https://idp.grips.ac.jp/idp/shibboleth", "Kanto", "National Graduate Institute for Policy Studies", "National Graduate Institute for Policy Studies", "政策研究大学院大学"],
        SAML1SSOurl: "https://idp.grips.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakuninshib.tmu.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo Metropolitan University",
        search: ["https://gakuninshib.tmu.ac.jp/idp/shibboleth", "Kanto", "Tokyo Metropolitan University", "Tokyo Metropolitan University", "首都大学東京"],
        SAML1SSOurl: "https://gakuninshib.tmu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp-gakunin.nap.gsic.titech.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo Institute of Technology",
        search: ["https://idp-gakunin.nap.gsic.titech.ac.jp/idp/shibboleth", "Kanto", "Tokyo Institute of Technology", "Tokyo Institute of Technology", "東京工業大学"],
        SAML1SSOurl: "https://idp-gakunin.nap.gsic.titech.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.tsurumi-u.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tsurumi University",
        search: ["https://idp.tsurumi-u.ac.jp/idp/shibboleth", "Kanto", "Tsurumi University", "Tsurumi University", "鶴見大学"],
        SAML1SSOurl: "https://idp.tsurumi-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://sidp.ibaraki.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Ibaraki University",
        search: ["https://sidp.ibaraki.ac.jp/idp/shibboleth", "Kanto", "Ibaraki University", "Ibaraki University", "茨城大学"],
        SAML1SSOurl: "https://sidp.ibaraki.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.nims.go.jp/idp/shibboleth": {
        type: "kanto",
        name: "National Institute for Materials Science",
        search: ["https://idp.nims.go.jp/idp/shibboleth", "Kanto", "National Institute for Materials Science", "National Institute for Materials Science", "物質・材料研究機構"],
        SAML1SSOurl: "https://idp.nims.go.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.toyaku.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo University of Pharmacy and Life Sciences",
        search: ["https://idp.toyaku.ac.jp/idp/shibboleth", "Kanto", "Tokyo University of Pharmacy and Life Sciences", "Tokyo University of Pharmacy and Life Sciences", "東京薬科大学"],
        SAML1SSOurl: "https://idp.toyaku.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin2.tuat.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo University of Agriculture and Technology",
        search: ["https://gakunin2.tuat.ac.jp/idp/shibboleth", "Kanto", "Tokyo University of Agriculture and Technology", "Tokyo University of Agriculture and Technology", "東京農工大学"],
        SAML1SSOurl: "https://gakunin2.tuat.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin-idp.shodai.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Yokohama College of Commerce",
        search: ["https://gakunin-idp.shodai.ac.jp/idp/shibboleth", "Kanto", "Yokohama College of Commerce", "Yokohama College of Commerce", "横浜商科大学"],
        SAML1SSOurl: "https://gakunin-idp.shodai.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://koma-sso.komazawa-u.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Komazawa University",
        search: ["https://koma-sso.komazawa-u.ac.jp/idp/shibboleth", "Kanto", "Komazawa University", "Komazawa University", "駒澤大学"],
        SAML1SSOurl: "https://koma-sso.komazawa-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp3.qst.go.jp/idp/shibboleth": {
        type: "kanto",
        name: "National Institutes for Quantum and Radiological Science and Technology",
        search: ["https://idp3.qst.go.jp/idp/shibboleth", "Kanto", "National Institutes for Quantum and Radiological Science and Technology", "National Institutes for Quantum and Radiological Science and Technology", "量子科学技術研究開発機構"],
        SAML1SSOurl: "https://idp3.qst.go.jp/idp/profile/Shibboleth/SSO"
    },
    "https://rprx.rku.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Ryutsu Keizai University",
        search: ["https://rprx.rku.ac.jp/idp/shibboleth", "Kanto", "Ryutsu Keizai University", "Ryutsu Keizai University", "流通経済大学"],
        SAML1SSOurl: "https://rprx.rku.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.kanagawa-u.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Kanagawa University",
        search: ["https://idp.kanagawa-u.ac.jp/idp/shibboleth", "Kanto", "Kanagawa University", "Kanagawa University", "神奈川大学"],
        SAML1SSOurl: "https://no.saml1.sso.url.defined.com/error"
    },
    "https://idp.ide.go.jp/idp/shibboleth": {
        type: "kanto",
        name: "IDE-JETRO",
        search: ["https://idp.ide.go.jp/idp/shibboleth", "Kanto", "IDE-JETRO", "IDE-JETRO", "アジア経済研究所"],
        SAML1SSOurl: "https://idp.ide.go.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.senshu-u.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Senshu University",
        search: ["https://idp.senshu-u.ac.jp/idp/shibboleth", "Kanto", "Senshu University", "Senshu University", "専修大学"],
        SAML1SSOurl: "https://idp.senshu-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.geidai.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Tokyo University of the Arts",
        search: ["https://idp.geidai.ac.jp/idp/shibboleth", "Kanto", "Tokyo University of the Arts", "Tokyo University of the Arts", "東京藝術大学"],
        SAML1SSOurl: "https://idp.geidai.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.aoyama.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Aoyama Gakuin University",
        search: ["https://idp.aoyama.ac.jp/idp/shibboleth", "Kanto", "Aoyama Gakuin University", "Aoyama Gakuin University", "青山学院大学"],
        SAML1SSOurl: "https://idp.aoyama.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://sso.internet.ac.jp": {
        type: "kanto",
        name: "Tokyo Online University",
        search: ["https://sso.internet.ac.jp", "Kanto", "Tokyo Online University", "Tokyo Online University", "東京通信大学"],
        SAML1SSOurl: "https://no.saml1.sso.url.defined.com/error"
    },
    "https://idp.itc.saitama-u.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Saitama University",
        search: ["https://idp.itc.saitama-u.ac.jp/idp/shibboleth", "Kanto", "Saitama University", "Saitama University", "埼玉大学"],
        SAML1SSOurl: "https://idp.itc.saitama-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://lib.nmct.ntt-east.co.jp/idp/shibboleth": {
        type: "kanto",
        name: "NTT Medical Center Tokyo Library",
        search: ["https://lib.nmct.ntt-east.co.jp/idp/shibboleth", "Kanto", "NTT Medical Center Tokyo Library", "NTT Medical Center Tokyo Library", "NTT東日本関東病院図書館"],
        SAML1SSOurl: "https://lib.nmct.ntt-east.co.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.my-pharm.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Meiji Pharmaceutical University",
        search: ["https://idp.my-pharm.ac.jp/idp/shibboleth", "Kanto", "Meiji Pharmaceutical University", "Meiji Pharmaceutical University", "明治薬科大学"],
        SAML1SSOurl: "https://idp.my-pharm.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin.st.daito.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Daito Bunka University",
        search: ["https://gakunin.st.daito.ac.jp/idp/shibboleth", "Kanto", "Daito Bunka University", "Daito Bunka University", "大東文化大学"],
        SAML1SSOurl: "https://gakunin.st.daito.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.kiryu-u.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Kiryu University",
        search: ["https://idp.kiryu-u.ac.jp/idp/shibboleth", "Kanto", "Kiryu University", "Kiryu University", "桐生大学"],
        SAML1SSOurl: "https://idp.kiryu-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://slink.secioss.com/icu.ac.jp": {
        type: "kanto",
        name: "International Christian University",
        search: ["https://slink.secioss.com/icu.ac.jp", "Kanto", "International Christian University", "International Christian University", "国際基督教大学"],
        SAML1SSOurl: "https://no.saml1.sso.url.defined.com/error"
    },
    "https://iaidp.ia.waseda.jp/idp/shibboleth": {
        type: "kanto",
        name: "Waseda University",
        search: ["https://iaidp.ia.waseda.jp/idp/shibboleth", "Kanto", "Waseda University", "Waseda University", "早稲田大学"],
        SAML1SSOurl: "https://iaidp.ia.waseda.jp/idp/profile/Shibboleth/SSO"
    },
    "https://sh-idp.riken.jp/idp/shibboleth": {
        type: "kanto",
        name: "RIKEN",
        search: ["https://sh-idp.riken.jp/idp/shibboleth", "Kanto", "RIKEN", "RIKEN", "理化学研究所"],
        SAML1SSOurl: "https://sh-idp.riken.jp/idp/profile/Shibboleth/SSO"
    },
    "https://obirin.ex-tic.com/auth/gakunin/saml2/assertions": {
        type: "kanto",
        name: "J. F. Oberlin University",
        search: ["https://obirin.ex-tic.com/auth/gakunin/saml2/assertions", "Kanto", "J. F. Oberlin University", "J. F. Oberlin University", "桜美林大学"],
        SAML1SSOurl: "https://no.saml1.sso.url.defined.com/error"
    },
    "https://idp.jichi.ac.jp/idp/shibboleth": {
        type: "kanto",
        name: "Jichi Medical University",
        search: ["https://idp.jichi.ac.jp/idp/shibboleth", "Kanto", "Jichi Medical University", "Jichi Medical University", "自治医科大学"],
        SAML1SSOurl: "https://idp.jichi.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://fed.mie-u.ac.jp/idp": {
        type: "chubu",
        name: "Mie University",
        search: ["https://fed.mie-u.ac.jp/idp", "Chubu", "Mie University", "Mie University", "三重大学"],
        SAML1SSOurl: "https://fed.mie-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin.ealps.shinshu-u.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Shinshu University",
        search: ["https://gakunin.ealps.shinshu-u.ac.jp/idp/shibboleth", "Chubu", "Shinshu University", "Shinshu University", "信州大学"],
        SAML1SSOurl: "https://gakunin.ealps.shinshu-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gknidp.ict.nitech.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Nagoya Institute of Technology",
        search: ["https://gknidp.ict.nitech.ac.jp/idp/shibboleth", "Chubu", "Nagoya Institute of Technology", "Nagoya Institute of Technology", "名古屋工業大学"],
        SAML1SSOurl: "https://gknidp.ict.nitech.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.yamanashi.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "University of Yamanashi",
        search: ["https://idp.yamanashi.ac.jp/idp/shibboleth", "Chubu", "University of Yamanashi", "University of Yamanashi", "山梨大学"],
        SAML1SSOurl: "https://idp.yamanashi.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.suzuka-ct.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "National Institute of Technology,Suzuka College",
        search: ["https://idp.suzuka-ct.ac.jp/idp/shibboleth", "Chubu", "National Institute of Technology,Suzuka College", "National Institute of Technology,Suzuka College", "鈴鹿工業高等専門学校"],
        SAML1SSOurl: "https://idp.suzuka-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.imc.tut.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Toyohashi University of Technology",
        search: ["https://idp.imc.tut.ac.jp/idp/shibboleth", "Chubu", "Toyohashi University of Technology", "Toyohashi University of Technology", "豊橋技術科学大学"],
        SAML1SSOurl: "https://idp.imc.tut.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.fukui-nct.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "National Institute of Technology,Fukui College",
        search: ["https://kidp.fukui-nct.ac.jp/idp/shibboleth", "Chubu", "National Institute of Technology,Fukui College", "National Institute of Technology,Fukui College", "福井工業高等専門学校"],
        SAML1SSOurl: "https://kidp.fukui-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.shizuoka.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Shizuoka University",
        search: ["https://idp.shizuoka.ac.jp/idp/shibboleth", "Chubu", "Shizuoka University", "Shizuoka University", "静岡大学"],
        SAML1SSOurl: "https://idp.shizuoka.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://wagner.isc.chubu.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "CHUBU UNIVERSITY",
        search: ["https://wagner.isc.chubu.ac.jp/idp/shibboleth", "Chubu", "CHUBU UNIVERSITY", "CHUBU UNIVERSITY", "中部大学"],
        SAML1SSOurl: "https://wagner.isc.chubu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.nagaoka-ct.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "National Institute of Technology,Nagaoka College",
        search: ["https://kidp.nagaoka-ct.ac.jp/idp/shibboleth", "Chubu", "National Institute of Technology,Nagaoka College", "National Institute of Technology,Nagaoka College", "長岡工業高等専門学校"],
        SAML1SSOurl: "https://kidp.nagaoka-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.numazu-ct.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "National Institute of Technology,Numazu College",
        search: ["https://kidp.numazu-ct.ac.jp/idp/shibboleth", "Chubu", "National Institute of Technology,Numazu College", "National Institute of Technology,Numazu College", "沼津工業高等専門学校"],
        SAML1SSOurl: "https://kidp.numazu-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.nagano-nct.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "National Institute of Technology,Nagano College",
        search: ["https://kidp.nagano-nct.ac.jp/idp/shibboleth", "Chubu", "National Institute of Technology,Nagano College", "National Institute of Technology,Nagano College", "長野工業高等専門学校"],
        SAML1SSOurl: "https://kidp.nagano-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.ishikawa-nct.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "National Institute of Technology,Ishikawa College",
        search: ["https://kidp.ishikawa-nct.ac.jp/idp/shibboleth", "Chubu", "National Institute of Technology,Ishikawa College", "National Institute of Technology,Ishikawa College", "石川工業高等専門学校"],
        SAML1SSOurl: "https://kidp.ishikawa-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kiidp.nc-toyama.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "National Institute of Technology,Toyama College",
        search: ["https://kiidp.nc-toyama.ac.jp/idp/shibboleth", "Chubu", "National Institute of Technology,Toyama College", "National Institute of Technology,Toyama College", "富山高等専門学校"],
        SAML1SSOurl: "https://kiidp.nc-toyama.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.toba-cmt.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "National Institute of Technology,Toba College",
        search: ["https://kidp.toba-cmt.ac.jp/idp/shibboleth", "Chubu", "National Institute of Technology,Toba College", "National Institute of Technology,Toba College", "鳥羽商船高等専門学校"],
        SAML1SSOurl: "https://kidp.toba-cmt.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.gifu-nct.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "National Institute of Technology,Gifu College",
        search: ["https://kidp.gifu-nct.ac.jp/idp/shibboleth", "Chubu", "National Institute of Technology,Gifu College", "National Institute of Technology,Gifu College", "岐阜工業高等専門学校"],
        SAML1SSOurl: "https://kidp.gifu-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://sso.sugiyama-u.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Sugiyama Jogakuen University",
        search: ["https://sso.sugiyama-u.ac.jp/idp/shibboleth", "Chubu", "Sugiyama Jogakuen University", "Sugiyama Jogakuen University", "椙山女学園大学"],
        SAML1SSOurl: "https://sso.sugiyama-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.toyota-ct.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "National Institute of Technology,Toyota College",
        search: ["https://kidp.toyota-ct.ac.jp/idp/shibboleth", "Chubu", "National Institute of Technology,Toyota College", "National Institute of Technology,Toyota College", "豊田工業高等専門学校"],
        SAML1SSOurl: "https://kidp.toyota-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shib.nagoya-u.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Nagoya University",
        search: ["https://shib.nagoya-u.ac.jp/idp/shibboleth", "Chubu", "Nagoya University", "Nagoya University", "名古屋大学"],
        SAML1SSOurl: "https://shib.nagoya-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://islwpi01.auecc.aichi-edu.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Aichi University of Education",
        search: ["https://islwpi01.auecc.aichi-edu.ac.jp/idp/shibboleth", "Chubu", "Aichi University of Education", "Aichi University of Education", "愛知教育大学"],
        SAML1SSOurl: "https://islwpi01.auecc.aichi-edu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://ams.juen.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Joetsu University of Education",
        search: ["https://ams.juen.ac.jp/idp/shibboleth", "Chubu", "Joetsu University of Education", "Joetsu University of Education", "上越教育大学"],
        SAML1SSOurl: "https://no.saml1.sso.url.defined.com/error"
    },
    "https://idp1.b.cii.u-fukui.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "University of Fukui",
        search: ["https://idp1.b.cii.u-fukui.ac.jp/idp/shibboleth", "Chubu", "University of Fukui", "University of Fukui", "福井大学"],
        SAML1SSOurl: "https://idp1.b.cii.u-fukui.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin.gifu-u.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Gifu University",
        search: ["https://gakunin.gifu-u.ac.jp/idp/shibboleth", "Chubu", "Gifu University", "Gifu University", "岐阜大学"],
        SAML1SSOurl: "https://gakunin.gifu-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.iamas.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Institute of Advanced Media Arts and Sciences",
        search: ["https://idp.iamas.ac.jp/idp/shibboleth", "Chubu", "Institute of Advanced Media Arts and Sciences", "Institute of Advanced Media Arts and Sciences", "情報科学芸術大学院大学"],
        SAML1SSOurl: "https://idp.iamas.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin.aitech.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Aichi Institute of Technology",
        search: ["https://gakunin.aitech.ac.jp/idp/shibboleth", "Chubu", "Aichi Institute of Technology", "Aichi Institute of Technology", "愛知工業大学"],
        SAML1SSOurl: "https://gakunin.aitech.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://ipcm2.nagaokaut.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Nagaoka University of Technology",
        search: ["https://ipcm2.nagaokaut.ac.jp/idp/shibboleth", "Chubu", "Nagaoka University of Technology", "Nagaoka University of Technology", "長岡技術科学大学"],
        SAML1SSOurl: "https://ipcm2.nagaokaut.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shibboleth.niigata-cn.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Niigata College of Nursing",
        search: ["https://shibboleth.niigata-cn.ac.jp/idp/shibboleth", "Chubu", "Niigata College of Nursing", "Niigata College of Nursing", "新潟県立看護大学"],
        SAML1SSOurl: "https://shibboleth.niigata-cn.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.nifs.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "National Institute for Fusion Science",
        search: ["https://idp.nifs.ac.jp/idp/shibboleth", "Chubu", "National Institute for Fusion Science", "National Institute for Fusion Science", "核融合科学研究所"],
        SAML1SSOurl: "https://idp.nifs.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shib.chukyo-u.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "CHUKYO UNIVERSITY",
        search: ["https://shib.chukyo-u.ac.jp/idp/shibboleth", "Chubu", "CHUKYO UNIVERSITY", "CHUKYO UNIVERSITY", "中京大学"],
        SAML1SSOurl: "https://shib.chukyo-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.cais.niigata-u.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Niigata University",
        search: ["https://idp.cais.niigata-u.ac.jp/idp/shibboleth", "Chubu", "Niigata University", "Niigata University", "新潟大学"],
        SAML1SSOurl: "https://idp.cais.niigata-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.fujita-hu.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Fujita Health University",
        search: ["https://idp.fujita-hu.ac.jp/idp/shibboleth", "Chubu", "Fujita Health University", "Fujita Health University", "藤田医科大学"],
        SAML1SSOurl: "https://idp.fujita-hu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://ku-sso.cis.kanazawa-u.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Kanazawa University",
        search: ["https://ku-sso.cis.kanazawa-u.ac.jp/idp/shibboleth", "Chubu", "Kanazawa University", "Kanazawa University", "金沢大学"],
        SAML1SSOurl: "https://ku-sso.cis.kanazawa-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.gifu.shotoku.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Gifu Shotoku Gakuen University",
        search: ["https://idp.gifu.shotoku.ac.jp/idp/shibboleth", "Chubu", "Gifu Shotoku Gakuen University", "Gifu Shotoku Gakuen University", "岐阜聖徳学園大学"],
        SAML1SSOurl: "https://idp.gifu.shotoku.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp02.u-toyama.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "University of Toyama",
        search: ["https://idp02.u-toyama.ac.jp/idp/shibboleth", "Chubu", "University of Toyama", "University of Toyama", "富山大学"],
        SAML1SSOurl: "https://idp02.u-toyama.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin.ims.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Institute for Molecular Science",
        search: ["https://gakunin.ims.ac.jp/idp/shibboleth", "Chubu", "Institute for Molecular Science", "Institute for Molecular Science", "分子科学研究所"],
        SAML1SSOurl: "https://gakunin.ims.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.tsuru.ac.jp/idp/shibboleth": {
        type: "chubu",
        name: "Tsuru University",
        search: ["https://idp.tsuru.ac.jp/idp/shibboleth", "Chubu", "Tsuru University", "Tsuru University", "都留文科大学"],
        SAML1SSOurl: "https://idp.tsuru.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://authidp1.iimc.kyoto-u.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kyoto University",
        search: ["https://authidp1.iimc.kyoto-u.ac.jp/idp/shibboleth", "Kinki", "Kyoto University", "Kyoto University", "京都大学"],
        SAML1SSOurl: "https://authidp1.iimc.kyoto-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin.kyoto-su.ac.jp/idp": {
        type: "kinki",
        name: "Kyoto Sangyo University",
        search: ["https://gakunin.kyoto-su.ac.jp/idp", "Kinki", "Kyoto Sangyo University", "Kyoto Sangyo University", "京都産業大学"],
        SAML1SSOurl: "https://gakunin.kyoto-su.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://fed.center.kobe-u.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kobe University",
        search: ["https://fed.center.kobe-u.ac.jp/idp/shibboleth", "Kinki", "Kobe University", "Kobe University", "神戸大学"],
        SAML1SSOurl: "https://fed.center.kobe-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.naist.jp/idp/shibboleth": {
        type: "kinki",
        name: "Nara Institute of Science and Technology",
        search: ["https://idp.naist.jp/idp/shibboleth", "Kinki", "Nara Institute of Science and Technology", "Nara Institute of Science and Technology", "奈良先端科学技術大学院大学"],
        SAML1SSOurl: "https://idp.naist.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shib-idp.nara-edu.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Nara University of Education",
        search: ["https://shib-idp.nara-edu.ac.jp/idp/shibboleth", "Kinki", "Nara University of Education", "Nara University of Education", "奈良教育大学"],
        SAML1SSOurl: "https://shib-idp.nara-edu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.ritsumei.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Ritsumeikan University",
        search: ["https://idp.ritsumei.ac.jp/idp/shibboleth", "Kinki", "Ritsumeikan University", "Ritsumeikan University", "立命館大学"],
        SAML1SSOurl: "https://idp.ritsumei.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp1.itc.kansai-u.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kansai University",
        search: ["https://idp1.itc.kansai-u.ac.jp/idp/shibboleth", "Kinki", "Kansai University", "Kansai University", "関西大学"],
        SAML1SSOurl: "https://idp1.itc.kansai-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shib.osaka-kyoiku.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Osaka Kyoiku University",
        search: ["https://shib.osaka-kyoiku.ac.jp/idp/shibboleth", "Kinki", "Osaka Kyoiku University", "Osaka Kyoiku University", "大阪教育大学"],
        SAML1SSOurl: "https://shib.osaka-kyoiku.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp1.kyokyo-u.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kyoto University of Education",
        search: ["https://idp1.kyokyo-u.ac.jp/idp/shibboleth", "Kinki", "Kyoto University of Education", "Kyoto University of Education", "京都教育大学"],
        SAML1SSOurl: "https://idp1.kyokyo-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://authsv.kpu.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kyoto Prefectural University",
        search: ["https://authsv.kpu.ac.jp/idp/shibboleth", "Kinki", "Kyoto Prefectural University", "Kyoto Prefectural University", "京都府立大学"],
        SAML1SSOurl: "https://authsv.kpu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.tezukayama-u.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "TEZUKAYAMA UNIVERSITY",
        search: ["https://idp.tezukayama-u.ac.jp/idp/shibboleth", "Kinki", "TEZUKAYAMA UNIVERSITY", "TEZUKAYAMA UNIVERSITY", "帝塚山大学"],
        SAML1SSOurl: "https://idp.tezukayama-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.tieskun.net/idp/shibboleth": {
        type: "kinki",
        name: "CCC-TIES",
        search: ["https://idp.tieskun.net/idp/shibboleth", "Kinki", "CCC-TIES", "CCC-TIES", "CCC-TIES"],
        SAML1SSOurl: "https://idp.tieskun.net/idp/profile/Shibboleth/SSO"
    },
    "https://idp.ouhs.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Osaka University of Health and Sport Sciences",
        search: ["https://idp.ouhs.ac.jp/idp/shibboleth", "Kinki", "Osaka University of Health and Sport Sciences", "Osaka University of Health and Sport Sciences", "大阪体育大学"],
        SAML1SSOurl: "https://idp.ouhs.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.maizuru-ct.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "National Institute of Technology,Maizuru College",
        search: ["https://kidp.maizuru-ct.ac.jp/idp/shibboleth", "Kinki", "National Institute of Technology,Maizuru College", "National Institute of Technology,Maizuru College", "舞鶴工業高等専門学校"],
        SAML1SSOurl: "https://kidp.maizuru-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.wakayama-nct.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "National Institute of Technology,Wakayama College",
        search: ["https://kidp.wakayama-nct.ac.jp/idp/shibboleth", "Kinki", "National Institute of Technology,Wakayama College", "National Institute of Technology,Wakayama College", "和歌山工業高等専門学校"],
        SAML1SSOurl: "https://kidp.wakayama-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.akashi.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "National Institute of Technology,Akashi College",
        search: ["https://kidp.akashi.ac.jp/idp/shibboleth", "Kinki", "National Institute of Technology,Akashi College", "National Institute of Technology,Akashi College", "明石工業高等専門学校"],
        SAML1SSOurl: "https://kidp.akashi.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://g-shib.auth.oit.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Osaka Institute of Technology",
        search: ["https://g-shib.auth.oit.ac.jp/idp/shibboleth", "Kinki", "Osaka Institute of Technology", "Osaka Institute of Technology", "大阪工業大学"],
        SAML1SSOurl: "https://g-shib.auth.oit.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.nara-k.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "National Institute of Technology,Nara College",
        search: ["https://kidp.nara-k.ac.jp/idp/shibboleth", "Kinki", "National Institute of Technology,Nara College", "National Institute of Technology,Nara College", "奈良工業高等専門学校"],
        SAML1SSOurl: "https://kidp.nara-k.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.kobe-cufs.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kobe City University of Foreign Studies",
        search: ["https://idp.kobe-cufs.ac.jp/idp/shibboleth", "Kinki", "Kobe City University of Foreign Studies", "Kobe City University of Foreign Studies", "神戸市外国語大学"],
        SAML1SSOurl: "https://idp.kobe-cufs.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://sumsidp.shiga-med.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Shiga University of Medical Science",
        search: ["https://sumsidp.shiga-med.ac.jp/idp/shibboleth", "Kinki", "Shiga University of Medical Science", "Shiga University of Medical Science", "滋賀医科大学"],
        SAML1SSOurl: "https://sumsidp.shiga-med.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.kobe-tokiwa.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kobe Tokiwa University",
        search: ["https://idp.kobe-tokiwa.ac.jp/idp/shibboleth", "Kinki", "Kobe Tokiwa University", "Kobe Tokiwa University", "神戸常盤大学"],
        SAML1SSOurl: "https://idp.kobe-tokiwa.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gakunin.osaka-cu.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Osaka City University",
        search: ["https://gakunin.osaka-cu.ac.jp/idp/shibboleth", "Kinki", "Osaka City University", "Osaka City University", "大阪市立大学"],
        SAML1SSOurl: "https://gakunin.osaka-cu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.doshisha.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Doshisha University",
        search: ["https://idp.doshisha.ac.jp/idp/shibboleth", "Kinki", "Doshisha University", "Doshisha University", "同志社大学"],
        SAML1SSOurl: "https://idp.doshisha.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.kpu-m.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kyoto Prefectural University of Medicine",
        search: ["https://idp.kpu-m.ac.jp/idp/shibboleth", "Kinki", "Kyoto Prefectural University of Medicine", "Kyoto Prefectural University of Medicine", "京都府立医科大学"],
        SAML1SSOurl: "https://idp.kpu-m.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.otani.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Otani University",
        search: ["https://idp.otani.ac.jp/idp/shibboleth", "Kinki", "Otani University", "Otani University", "大谷大学"],
        SAML1SSOurl: "https://idp.otani.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gidp.ryukoku.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Ryukoku University",
        search: ["https://gidp.ryukoku.ac.jp/idp/shibboleth", "Kinki", "Ryukoku University", "Ryukoku University", "龍谷大学"],
        SAML1SSOurl: "https://gidp.ryukoku.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://naraidp.cc.nara-wu.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Nara Women\'s University",
        search: ["https://naraidp.cc.nara-wu.ac.jp/idp/shibboleth", "Kinki", "Nara Women\'s University", "Nara Women\'s University", "奈良女子大学"],
        SAML1SSOurl: "https://naraidp.cc.nara-wu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gk-idp.auth.osaka-u.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Osaka University",
        search: ["https://gk-idp.auth.osaka-u.ac.jp/idp/shibboleth", "Kinki", "Osaka University", "Osaka University", "大阪大学"],
        SAML1SSOurl: "https://gk-idp.auth.osaka-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://heimdall.osaka-aoyama.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Osaka Aoyama University",
        search: ["https://heimdall.osaka-aoyama.ac.jp/idp/shibboleth", "Kinki", "Osaka Aoyama University", "Osaka Aoyama University", "大阪青山大学"],
        SAML1SSOurl: "https://heimdall.osaka-aoyama.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.kindai.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kindai University",
        search: ["https://idp.kindai.ac.jp/idp/shibboleth", "Kinki", "Kindai University", "Kindai University", "近畿大学"],
        SAML1SSOurl: "https://idp.kindai.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.cis.kit.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kyoto Institute of Technology",
        search: ["https://idp.cis.kit.ac.jp/idp/shibboleth", "Kinki", "Kyoto Institute of Technology", "Kyoto Institute of Technology", "京都工芸繊維大学"],
        SAML1SSOurl: "https://idp.cis.kit.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.andrew.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Momoyama Gakuin University",
        search: ["https://idp.andrew.ac.jp/idp/shibboleth", "Kinki", "Momoyama Gakuin University", "Momoyama Gakuin University", "桃山学院大学"],
        SAML1SSOurl: "https://idp.andrew.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.kobe-ccn.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kobe City College of Nursing",
        search: ["https://idp.kobe-ccn.ac.jp/idp/shibboleth", "Kinki", "Kobe City College of Nursing", "Kobe City College of Nursing", "神戸市看護大学"],
        SAML1SSOurl: "https://idp.kobe-ccn.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.u-hyogo.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "University of Hyogo",
        search: ["https://idp.u-hyogo.ac.jp/idp/shibboleth", "Kinki", "University of Hyogo", "University of Hyogo", "兵庫県立大学"],
        SAML1SSOurl: "https://idp.u-hyogo.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.wakayama-u.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Wakayama University",
        search: ["https://idp.wakayama-u.ac.jp/idp/shibboleth", "Kinki", "Wakayama University", "Wakayama University", "和歌山大学"],
        SAML1SSOurl: "https://idp.wakayama-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.21c.osakafu-u.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Osaka Prefecture University",
        search: ["https://idp.21c.osakafu-u.ac.jp/idp/shibboleth", "Kinki", "Osaka Prefecture University", "Osaka Prefecture University", "大阪府立大学"],
        SAML1SSOurl: "https://idp.21c.osakafu-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://dc-shibsv.shiga-u.ac.jp/idp/shibboleth/": {
        type: "kinki",
        name: "SHIGA UNIVERSITY",
        search: ["https://dc-shibsv.shiga-u.ac.jp/idp/shibboleth/", "Kinki", "SHIGA UNIVERSITY", "SHIGA UNIVERSITY", "滋賀大学"],
        SAML1SSOurl: "https://dc-shibsv.shiga-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gkn.kbu.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Kyoto Bunkyo University",
        search: ["https://gkn.kbu.ac.jp/idp/shibboleth", "Kinki", "Kyoto Bunkyo University", "Kyoto Bunkyo University", "京都文教大学"],
        SAML1SSOurl: "https://gkn.kbu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.osaka-ue.ac.jp/idp/shibboleth": {
        type: "kinki",
        name: "Osaka University of Economics",
        search: ["https://idp.osaka-ue.ac.jp/idp/shibboleth", "Kinki", "Osaka University of Economics", "Osaka University of Economics", "大阪経済大学"],
        SAML1SSOurl: "https://idp.osaka-ue.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.hiroshima-u.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Hiroshima University",
        search: ["https://idp.hiroshima-u.ac.jp/idp/shibboleth", "Chugoku", "Hiroshima University", "Hiroshima University", "広島大学"],
        SAML1SSOurl: "https://idp.hiroshima-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://odidp.cc.okayama-u.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Okayama University",
        search: ["https://odidp.cc.okayama-u.ac.jp/idp/shibboleth", "Chugoku", "Okayama University", "Okayama University", "岡山大学"],
        SAML1SSOurl: "https://odidp.cc.okayama-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://fed.ipc.hiroshima-cu.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Hiroshima City University",
        search: ["https://fed.ipc.hiroshima-cu.ac.jp/idp/shibboleth", "Chugoku", "Hiroshima City University", "Hiroshima City University", "広島市立大学"],
        SAML1SSOurl: "https://fed.ipc.hiroshima-cu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.it-hiroshima.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Hiroshima Institute of Technology",
        search: ["https://idp.it-hiroshima.ac.jp/idp/shibboleth", "Chugoku", "Hiroshima Institute of Technology", "Hiroshima Institute of Technology", "広島工業大学"],
        SAML1SSOurl: "https://idp.it-hiroshima.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.shudo-u.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Hiroshima Shudo University",
        search: ["https://idp.shudo-u.ac.jp/idp/shibboleth", "Chugoku", "Hiroshima Shudo University", "Hiroshima Shudo University", "広島修道大学"],
        SAML1SSOurl: "https://idp.shudo-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.oshima-k.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "National Institute of Technology,Oshima College",
        search: ["https://kidp.oshima-k.ac.jp/idp/shibboleth", "Chugoku", "National Institute of Technology,Oshima College", "National Institute of Technology,Oshima College", "大島商船高等専門学校"],
        SAML1SSOurl: "https://kidp.oshima-k.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.kure-nct.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "National Institute of Technology,Kure College",
        search: ["https://kidp.kure-nct.ac.jp/idp/shibboleth", "Chugoku", "National Institute of Technology,Kure College", "National Institute of Technology,Kure College", "呉工業高等専門学校"],
        SAML1SSOurl: "https://kidp.kure-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.hiroshima-cmt.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "National Institute of Technology,Hiroshima College",
        search: ["https://kidp.hiroshima-cmt.ac.jp/idp/shibboleth", "Chugoku", "National Institute of Technology,Hiroshima College", "National Institute of Technology,Hiroshima College", "広島商船高等専門学校"],
        SAML1SSOurl: "https://kidp.hiroshima-cmt.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.yonago-k.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "National Institute of Technology,Yonago College",
        search: ["https://kidp.yonago-k.ac.jp/idp/shibboleth", "Chugoku", "National Institute of Technology,Yonago College", "National Institute of Technology,Yonago College", "米子工業高等専門学校"],
        SAML1SSOurl: "https://kidp.yonago-k.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.tsuyama-ct.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "National Institute of Technology,Tsuyama College",
        search: ["https://kidp.tsuyama-ct.ac.jp/idp/shibboleth", "Chugoku", "National Institute of Technology,Tsuyama College", "National Institute of Technology,Tsuyama College", "津山工業高等専門学校"],
        SAML1SSOurl: "https://kidp.tsuyama-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.ube-k.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "National Institute of Technology,Ube College",
        search: ["https://kidp.ube-k.ac.jp/idp/shibboleth", "Chugoku", "National Institute of Technology,Ube College", "National Institute of Technology,Ube College", "宇部工業高等専門学校"],
        SAML1SSOurl: "https://kidp.ube-k.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.tokuyama.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "National Institute of Technology,Tokuyama College",
        search: ["https://kidp.tokuyama.ac.jp/idp/shibboleth", "Chugoku", "National Institute of Technology,Tokuyama College", "National Institute of Technology,Tokuyama College", "徳山工業高等専門学校"],
        SAML1SSOurl: "https://kidp.tokuyama.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.matsue-ct.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "National Institute of Technology,Matsue College",
        search: ["https://idp.matsue-ct.ac.jp/idp/shibboleth", "Chugoku", "National Institute of Technology,Matsue College", "National Institute of Technology,Matsue College", "松江工業高等専門学校"],
        SAML1SSOurl: "https://idp.matsue-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.tottori-u.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Tottori University",
        search: ["https://idp.tottori-u.ac.jp/idp/shibboleth", "Chugoku", "Tottori University", "Tottori University", "鳥取大学"],
        SAML1SSOurl: "https://idp.tottori-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.shimane-u.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Shimane University",
        search: ["https://idp.shimane-u.ac.jp/idp/shibboleth", "Chugoku", "Shimane University", "Shimane University", "島根大学"],
        SAML1SSOurl: "https://idp.shimane-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.oka-pu.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Okayama Prefectural University",
        search: ["https://idp.oka-pu.ac.jp/idp/shibboleth", "Chugoku", "Okayama Prefectural University", "Okayama Prefectural University", "岡山県立大学"],
        SAML1SSOurl: "https://idp.oka-pu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.pu-hiroshima.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Prefectural University of Hiroshima",
        search: ["https://idp.pu-hiroshima.ac.jp/idp/shibboleth", "Chugoku", "Prefectural University of Hiroshima", "Prefectural University of Hiroshima", "県立広島大学"],
        SAML1SSOurl: "https://idp.pu-hiroshima.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://auth.socu.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Sanyo-Onoda City University",
        search: ["https://auth.socu.ac.jp/idp/shibboleth", "Chugoku", "Sanyo-Onoda City University", "Sanyo-Onoda City University", "山陽小野田市立山口東京理科大学"],
        SAML1SSOurl: "https://auth.socu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.cc.yamaguchi-u.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Yamaguchi University",
        search: ["https://idp.cc.yamaguchi-u.ac.jp/idp/shibboleth", "Chugoku", "Yamaguchi University", "Yamaguchi University", "山口大学"],
        SAML1SSOurl: "https://idp.cc.yamaguchi-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.pub.ous.ac.jp/idp/shibboleth": {
        type: "chugoku",
        name: "Okayama University of Science",
        search: ["https://idp.pub.ous.ac.jp/idp/shibboleth", "Chugoku", "Okayama University of Science", "Okayama University of Science", "岡山理科大学"],
        SAML1SSOurl: "https://idp.pub.ous.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.cc.ehime-u.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "Ehime University",
        search: ["https://idp.cc.ehime-u.ac.jp/idp/shibboleth", "Shikoku", "Ehime University", "Ehime University", "愛媛大学"],
        SAML1SSOurl: "https://idp.cc.ehime-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://gidp.ait230.tokushima-u.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "Tokushima University",
        search: ["https://gidp.ait230.tokushima-u.ac.jp/idp/shibboleth", "Shikoku", "Tokushima University", "Tokushima University", "徳島大学"],
        SAML1SSOurl: "https://gidp.ait230.tokushima-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.kochi-ct.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "National Institute of Technology,Kochi College",
        search: ["https://kidp.kochi-ct.ac.jp/idp/shibboleth", "Shikoku", "National Institute of Technology,Kochi College", "National Institute of Technology,Kochi College", "高知工業高等専門学校"],
        SAML1SSOurl: "https://kidp.kochi-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://ktidp.kagawa-nct.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "National Institute of Technology,Kagawa College",
        search: ["https://ktidp.kagawa-nct.ac.jp/idp/shibboleth", "Shikoku", "National Institute of Technology,Kagawa College", "National Institute of Technology,Kagawa College", "香川高等専門学校"],
        SAML1SSOurl: "https://ktidp.kagawa-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.yuge.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "National Institute of Technology,Yuge College",
        search: ["https://kidp.yuge.ac.jp/idp/shibboleth", "Shikoku", "National Institute of Technology,Yuge College", "National Institute of Technology,Yuge College", "弓削商船高等専門学校"],
        SAML1SSOurl: "https://kidp.yuge.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.niihama-nct.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "National Institute of Technology,Niihama College",
        search: ["https://kidp.niihama-nct.ac.jp/idp/shibboleth", "Shikoku", "National Institute of Technology,Niihama College", "National Institute of Technology,Niihama College", "新居浜工業高等専門学校"],
        SAML1SSOurl: "https://kidp.niihama-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.anan-nct.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "National Institute of Technology,Anan College",
        search: ["https://kidp.anan-nct.ac.jp/idp/shibboleth", "Shikoku", "National Institute of Technology,Anan College", "National Institute of Technology,Anan College", "阿南工業高等専門学校"],
        SAML1SSOurl: "https://kidp.anan-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.kochi-tech.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "Kochi University of Technology",
        search: ["https://idp.kochi-tech.ac.jp/idp/shibboleth", "Shikoku", "Kochi University of Technology", "Kochi University of Technology", "高知工科大学"],
        SAML1SSOurl: "https://idp.kochi-tech.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://aries.naruto-u.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "Naruto University of Education",
        search: ["https://aries.naruto-u.ac.jp/idp/shibboleth", "Shikoku", "Naruto University of Education", "Naruto University of Education", "鳴門教育大学"],
        SAML1SSOurl: "https://aries.naruto-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp1.matsuyama-u.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "Matsuyama University",
        search: ["https://idp1.matsuyama-u.ac.jp/idp/shibboleth", "Shikoku", "Matsuyama University", "Matsuyama University", "松山大学"],
        SAML1SSOurl: "https://idp1.matsuyama-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.kochi-u.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "Kochi University",
        search: ["https://idp.kochi-u.ac.jp/idp/shibboleth", "Shikoku", "Kochi University", "Kochi University", "高知大学"],
        SAML1SSOurl: "https://idp.kochi-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.itc.kagawa-u.ac.jp/idp/shibboleth": {
        type: "shikoku",
        name: "Kagawa University",
        search: ["https://idp.itc.kagawa-u.ac.jp/idp/shibboleth", "Shikoku", "Kagawa University", "Kagawa University", "香川大学"],
        SAML1SSOurl: "https://idp.itc.kagawa-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://ssoidp.cc.saga-u.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Saga University",
        search: ["https://ssoidp.cc.saga-u.ac.jp/idp/shibboleth", "Kyushu", "Saga University", "Saga University", "佐賀大学"],
        SAML1SSOurl: "https://ssoidp.cc.saga-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.isc.kyutech.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Kyushu Institute of Technology",
        search: ["https://idp.isc.kyutech.ac.jp/idp/shibboleth", "Kyushu", "Kyushu Institute of Technology", "Kyushu Institute of Technology", "九州工業大学"],
        SAML1SSOurl: "https://idp.isc.kyutech.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.kyushu-u.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Kyushu University",
        search: ["https://idp.kyushu-u.ac.jp/idp/shibboleth", "Kyushu", "Kyushu University", "Kyushu University", "九州大学"],
        SAML1SSOurl: "https://idp.kyushu-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://um-idp.cc.miyazaki-u.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "University of Miyazaki",
        search: ["https://um-idp.cc.miyazaki-u.ac.jp/idp/shibboleth", "Kyushu", "University of Miyazaki", "University of Miyazaki", "宮崎大学"],
        SAML1SSOurl: "https://um-idp.cc.miyazaki-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://fed.u-ryukyu.ac.jp/shibboleth": {
        type: "kyushu",
        name: "University of the Ryukyus",
        search: ["https://fed.u-ryukyu.ac.jp/shibboleth", "Kyushu", "University of the Ryukyus", "University of the Ryukyus", "琉球大学"],
        SAML1SSOurl: "https://fed.u-ryukyu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.kct.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "National Institute of Technology,Kitakyushu College",
        search: ["https://kidp.kct.ac.jp/idp/shibboleth", "Kyushu", "National Institute of Technology,Kitakyushu College", "National Institute of Technology,Kitakyushu College", "北九州工業高等専門学校"],
        SAML1SSOurl: "https://kidp.kct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shibboleth-idp.bene.fit.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Fukuoka Institute of Technology",
        search: ["https://shibboleth-idp.bene.fit.ac.jp/idp/shibboleth", "Kyushu", "Fukuoka Institute of Technology", "Fukuoka Institute of Technology", "福岡工業大学"],
        SAML1SSOurl: "https://shibboleth-idp.bene.fit.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shib.kumamoto-u.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Kumamoto University",
        search: ["https://shib.kumamoto-u.ac.jp/idp/shibboleth", "Kyushu", "Kumamoto University", "Kumamoto University", "熊本大学"],
        SAML1SSOurl: "https://shib.kumamoto-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.oita-ct.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "National Institute of Technology,Oita College",
        search: ["https://kidp.oita-ct.ac.jp/idp/shibboleth", "Kyushu", "National Institute of Technology,Oita College", "National Institute of Technology,Oita College", "大分工業高等専門学校"],
        SAML1SSOurl: "https://kidp.oita-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.sasebo.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "National Institute of Technology,Sasebo College",
        search: ["https://kidp.sasebo.ac.jp/idp/shibboleth", "Kyushu", "National Institute of Technology,Sasebo College", "National Institute of Technology,Sasebo College", "佐世保工業高等専門学校"],
        SAML1SSOurl: "https://kidp.sasebo.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.kagoshima-ct.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "National Institute of Technology,Kagoshima College",
        search: ["https://kidp.kagoshima-ct.ac.jp/idp/shibboleth", "Kyushu", "National Institute of Technology,Kagoshima College", "National Institute of Technology,Kagoshima College", "鹿児島工業高等専門学校"],
        SAML1SSOurl: "https://kidp.kagoshima-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.kurume-nct.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "National Institute of Technology,Kurume College",
        search: ["https://kidp.kurume-nct.ac.jp/idp/shibboleth", "Kyushu", "National Institute of Technology,Kurume College", "National Institute of Technology,Kurume College", "久留米工業高等専門学校"],
        SAML1SSOurl: "https://kidp.kurume-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.miyakonojo-nct.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "National Institute of Technology,Miyakonojo College",
        search: ["https://kidp.miyakonojo-nct.ac.jp/idp/shibboleth", "Kyushu", "National Institute of Technology,Miyakonojo College", "National Institute of Technology,Miyakonojo College", "都城工業高等専門学校"],
        SAML1SSOurl: "https://kidp.miyakonojo-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.ariake-nct.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "National Institute of Technology,Ariake College",
        search: ["https://kidp.ariake-nct.ac.jp/idp/shibboleth", "Kyushu", "National Institute of Technology,Ariake College", "National Institute of Technology,Ariake College", "有明工業高等専門学校"],
        SAML1SSOurl: "https://kidp.ariake-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.kumamoto-nct.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "National Institute of Technology,Kumamoto College",
        search: ["https://kidp.kumamoto-nct.ac.jp/idp/shibboleth", "Kyushu", "National Institute of Technology,Kumamoto College", "National Institute of Technology,Kumamoto College", "熊本高等専門学校"],
        SAML1SSOurl: "https://kidp.kumamoto-nct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.okinawa-ct.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "National Institute of Technology,Okinawa College",
        search: ["https://kidp.okinawa-ct.ac.jp/idp/shibboleth", "Kyushu", "National Institute of Technology,Okinawa College", "National Institute of Technology,Okinawa College", "沖縄工業高等専門学校"],
        SAML1SSOurl: "https://kidp.okinawa-ct.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://shibboleth-idp.kyusan-u.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Kyushu Sangyo University",
        search: ["https://shibboleth-idp.kyusan-u.ac.jp/idp/shibboleth", "Kyushu", "Kyushu Sangyo University", "Kyushu Sangyo University", "九州産業大学"],
        SAML1SSOurl: "https://shibboleth-idp.kyusan-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://logon.oist.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Okinawa Institute of Science and Technology Graduate University",
        search: ["https://logon.oist.jp/idp/shibboleth", "Kyushu", "Okinawa Institute of Science and Technology Graduate University", "Okinawa Institute of Science and Technology Graduate University", "沖縄科学技術大学院大学"],
        SAML1SSOurl: "https://logon.oist.jp/idp/profile/Shibboleth/SSO"
    },
    "https://nuidp.nagasaki-u.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Nagasaki University",
        search: ["https://nuidp.nagasaki-u.ac.jp/idp/shibboleth", "Kyushu", "Nagasaki University", "Nagasaki University", "長崎大学"],
        SAML1SSOurl: "https://nuidp.nagasaki-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.seinan-gu.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Seinan Gakuin University",
        search: ["https://idp.seinan-gu.ac.jp/idp/shibboleth", "Kyushu", "Seinan Gakuin University", "Seinan Gakuin University", "西南学院大学"],
        SAML1SSOurl: "https://idp.seinan-gu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.net.oita-u.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Oita University",
        search: ["https://idp.net.oita-u.ac.jp/idp/shibboleth", "Kyushu", "Oita University", "Oita University", "大分大学"],
        SAML1SSOurl: "https://idp.net.oita-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://kidp.cc.kagoshima-u.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Kagoshima University",
        search: ["https://kidp.cc.kagoshima-u.ac.jp/idp/shibboleth", "Kyushu", "Kagoshima University", "Kagoshima University", "鹿児島大学"],
        SAML1SSOurl: "https://kidp.cc.kagoshima-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.nifs-k.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "National Institute of Fitness and Sports in KANOYA",
        search: ["https://idp.nifs-k.ac.jp/idp/shibboleth", "Kyushu", "National Institute of Fitness and Sports in KANOYA", "National Institute of Fitness and Sports in KANOYA", "鹿屋体育大学"],
        SAML1SSOurl: "https://idp.nifs-k.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://ss.fukuoka-edu.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "University of Teacher Education Fukuoka",
        search: ["https://ss.fukuoka-edu.ac.jp/idp/shibboleth", "Kyushu", "University of Teacher Education Fukuoka", "University of Teacher Education Fukuoka", "福岡教育大学"],
        SAML1SSOurl: "https://ss.fukuoka-edu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.sun.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "University of Nagasaki",
        search: ["https://idp.sun.ac.jp/idp/shibboleth", "Kyushu", "University of Nagasaki", "University of Nagasaki", "長崎県立大学"],
        SAML1SSOurl: "https://idp.sun.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.okiu.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Okinawa International University",
        search: ["https://idp.okiu.ac.jp/idp/shibboleth", "Kyushu", "Okinawa International University", "Okinawa International University", "沖縄国際大学"],
        SAML1SSOurl: "https://idp.okiu.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.sojo-u.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "SOJO University",
        search: ["https://idp.sojo-u.ac.jp/idp/shibboleth", "Kyushu", "SOJO University", "SOJO University", "崇城大学"],
        SAML1SSOurl: "https://idp.sojo-u.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.kurume-it.ac.jp/idp/shibboleth": {
        type: "kyushu",
        name: "Kurume Institute of Technology",
        search: ["https://idp.kurume-it.ac.jp/idp/shibboleth", "Kyushu", "Kurume Institute of Technology", "Kurume Institute of Technology", "久留米工業大学"],
        SAML1SSOurl: "https://idp.kurume-it.ac.jp/idp/profile/Shibboleth/SSO"
    },
    "https://idp.gakunin.nii.ac.jp/idp/shibboleth": {
        type: "others",
        name: "GakuNin IdP",
        search: ["https://idp.gakunin.nii.ac.jp/idp/shibboleth", "Others", "GakuNin IdP", "GakuNin IdP", "学認IdP"],
        SAML1SSOurl: "https://idp.gakunin.nii.ac.jp/idp/profile/Shibboleth/SSO"
    }
};
var wayf_hint_list = [];
var inc_search_list = [];
var favorite_list = [];
var hint_list = [];
var submit_check_list = [];
var safekind = '2';
var allIdPList = '';
var initdisp = 'Select the Home Organisation you are affiliated with';
var dispDefault = '';
var dispidp = '';
var hiddenKeyText = '';
var dropdown_up = 'https://ds.gakunin.nii.ac.jp/GakuNinDS/images/dropdown_up.png';
var dropdown_down = 'https://ds.gakunin.nii.ac.jp/GakuNinDS/images/dropdown_down.png';
var favorite_idp_group = "Most often used Home Organisations";
var hint_idp_group = ' Hint! IdP';

// Add some property for GUI spec
var wayf_overwrite_submit_button_text = "ログイン";
var wayf_overwrite_checkbox_label_text = "ブラウザ起動中は自動ログイン";

var wayf_URL = "https://ds.gakunin.nii.ac.jp/WAYF";
var sp_domain = "https://idp.repo.nii.ac.jp";
var wayf_sp_entityID = sp_domain + "/shibboleth-sp";
var wayf_sp_handlerURL = sp_domain + "/Shibboleth.sso";
var wayf_return_url = sp_domain + "/loginproxy/getAuthInfo";
var wayf_discofeed_url = "https://ds.gakunin.nii.ac.jp/DiscoFeed/PS0054JP"; 
var wayf_width = "390";
var wayf_background_color = '#F8F8FF';
var wayf_font_color = '#000080';
var wayf_border_color = '#214890';

// Define functions
function submitForm() {

    var NonFedEntityID;
    var idp_name = document.getElementById('keytext').value.toLowerCase();
    var chkFlg = false;
    if (hiddenKeyText != '') idp_name = hiddenKeyText.toLowerCase();

    if (inc_search_list.length > 0) {
        submit_check_list = inc_search_list;
    }
    if (favorite_list.length > 0) {
        submit_check_list = favorite_list.concat(submit_check_list);
    }
    if (hint_list.length > 0) {
        submit_check_list = hint_list.concat(submit_check_list);
    }

    for (var i = 0; i < submit_check_list.length; i++) {
        for (var j = 3, len2 = submit_check_list[i].length; j < len2; j++) {
            var list_idp_name = submit_check_list[i][j].toLowerCase();
            if (idp_name == list_idp_name) {
                NonFedEntityID = submit_check_list[i][0];
                document.getElementById('user_idp').value = submit_check_list[i][0];
                chkFlg = true;
                if (safekind > 0 && safekind != 3) {
                    // Store SAML domain cookie for this foreign IdP
                    setCookie('_saml_idp', encodeBase64(submit_check_list[i][0]), 100);
                }
                break;
            }
        }
        if (chkFlg) {
            break;
        }
    }
    if (!chkFlg) {
        alert('You must select a valid Home Organisation.');
        return false;
    }

    // User chose non-federation IdP
    // TODO: FIX windows error
    // 4 >= (8 - 3/4)
    if (
        i >= (submit_check_list.length - wayf_additional_idps.length)) {

        var redirect_url;

        // Store SAML domain cookie for this foreign IdP
        setCookie('_saml_idp', encodeBase64(NonFedEntityID), 100);

        // Redirect user to SP handler
        if (wayf_use_discovery_service) {
            redirect_url = wayf_sp_samlDSURL + (wayf_sp_samlDSURL.indexOf('?') >= 0 ? '&' : '?') + 'entityID=' +
                encodeURIComponent(NonFedEntityID) +
                '&target=' + encodeURIComponent(wayf_return_url);

            // Make sure the redirect always is being done in parent window
            if (window.parent) {
                window.parent.location = redirect_url;
            } else {
                window.location = redirect_url;
            }

        } else {
            redirect_url = wayf_sp_handlerURL + '?providerId=' +
                encodeURIComponent(NonFedEntityID) +
                '&target=' + encodeURIComponent(wayf_return_url);

            // Make sure the redirect always is being done in parent window
            if (window.parent) {
                window.parent.location = redirect_url;
            } else {
                window.location = redirect_url;
            }

        }

        // If input type button is used for submit, we must return false
        return false;
    } else {
        if (safekind == 0 || safekind == 3) {
            // delete local cookie
            setCookie('_saml_idp', encodeBase64(submit_check_list[i][0]), -1);
        }
        // User chose federation IdP entry
        document.IdPList.submit();
    }
    return false;
}

function writeHTML(a) {
    wayf_html += a;
}

function pushIncSearchList(IdP) {
    inc_search_list.push(wayf_idps[IdP].search.slice());
    for (var i in wayf_hint_list) {
        if (wayf_hint_list[i] == IdP) {
            hint_list.push(wayf_idps[IdP].search.slice());
            hint_list[hint_list.length - 1][1] = hint_idp_group;
        }
    }
}

function isAllowedType(IdP, type) {
    for (var i = 0; i <= wayf_hide_categories.length; i++) {

        if (wayf_hide_categories[i] == type || wayf_hide_categories[i] == "all") {

            for (var i = 0; i <= wayf_unhide_idps.length; i++) {
                // Show IdP if it has to be unhidden
                if (wayf_unhide_idps[i] == IdP) {
                    return true;
                }
            }
            // If IdP is not unhidden, the default applies
            return false;
        }
    }

    // Category was not hidden
    return true;
}

function isAllowedCategory(category) {

    if (!category || category == '') {
        return true;
    }

    for (var i = 0; i <= wayf_hide_categories.length; i++) {

        if (wayf_hide_categories[i] == category || wayf_hide_categories[i] == "all") {
            return false;
        }
    }

    // Category was not hidden
    return true;
}

function isAllowedIdP(IdP) {

    for (var i = 0; i <= wayf_hide_idps.length; i++) {
        if (wayf_hide_idps[i] == IdP) {
            return false;
        }
    }
    // IdP was not hidden
    return true;
}

function setCookie(c_name, value, expiredays) {
    var exdate = new Date();
    exdate.setDate(exdate.getDate() + expiredays);
    document.cookie = c_name + "=" + escape(value) +
        ((expiredays == null) ? "" : "; expires=" + exdate.toGMTString()) +
        ((wayf_sp_cookie_path == "") ? "" : "; path=" + wayf_sp_cookie_path) + "; secure";
}

function getCookie(check_name) {
    // First we split the cookie up into name/value pairs
    // Note: document.cookie only returns name=value, not the other components
    var a_all_cookies = document.cookie.split(';');
    var a_temp_cookie = '';
    var cookie_name = '';
    var cookie_value = '';

    for (var i = 0; i < a_all_cookies.length; i++) {
        // now we'll split apart each name=value pair
        a_temp_cookie = a_all_cookies[i].split('=');


        // and trim left/right whitespace while we're at it
        cookie_name = a_temp_cookie[0].replace(/^\s+|\s+$/g, '');

        // if the extracted name matches passed check_name
        if (cookie_name == check_name) {
            // We need to handle case where cookie has no value but exists (no = sign, that is):
            if (a_temp_cookie.length > 1) {
                cookie_value = unescape(a_temp_cookie[1].replace(/^\s+|\s+$/g, ''));
            }
            // note that in cases where cookie is initialized but no value, null is returned
            return cookie_value;
            break;
        }
        a_temp_cookie = null;
        cookie_name = '';
    }

    return null;
}

// Checks if there exists a cookie containing check_name in its name
function isCookie(check_name) {
    // First we split the cookie up into name/value pairs
    // Note: document.cookie only returns name=value, not the other components
    var a_all_cookies = document.cookie.split(';');
    var a_temp_cookie = '';
    var cookie_name = '';

    for (var i = 0; i < a_all_cookies.length; i++) {
        // now we'll split apart each name=value pair
        a_temp_cookie = a_all_cookies[i].split('=');

        // and trim left/right whitespace while we're at it
        cookie_name = a_temp_cookie[0].replace(/^\s+|\s+$/g, '');

        // if the extracted name matches passed check_name

        if (cookie_name.search(check_name) >= 0) {
            return true;
        }
    }

    // Shibboleth session cookie has not been found
    return false;
}

function encodeBase64(input) {
    var base64chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
    var output = "",
        c1, c2, c3, e1, e2, e3, e4;

    for (var i = 0; i < input.length;) {
        c1 = input.charCodeAt(i++);
        c2 = input.charCodeAt(i++);
        c3 = input.charCodeAt(i++);
        e1 = c1 >> 2;
        e2 = ((c1 & 3) << 4) + (c2 >> 4);
        e3 = ((c2 & 15) << 2) + (c3 >> 6);
        e4 = c3 & 63;
        if (isNaN(c2)) {
            e3 = e4 = 64;
        } else if (isNaN(c3)) {
            e4 = 64;
        }
        output += base64chars.charAt(e1) + base64chars.charAt(e2) + base64chars.charAt(e3) + base64chars.charAt(e4);
    }

    return output;
}

function decodeBase64(input) {
    var base64chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
    var output = "",
        chr1, chr2, chr3, enc1, enc2, enc3, enc4;
    var i = 0;

    // Remove all characters that are not A-Z, a-z, 0-9, +, /, or =
    var base64test = /[^A-Za-z0-9\+\/\=]/g;
    input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

    do {
        enc1 = base64chars.indexOf(input.charAt(i++));
        enc2 = base64chars.indexOf(input.charAt(i++));
        enc3 = base64chars.indexOf(input.charAt(i++));
        enc4 = base64chars.indexOf(input.charAt(i++));

        chr1 = (enc1 << 2) | (enc2 >> 4);
        chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
        chr3 = ((enc3 & 3) << 6) | enc4;

        output = output + String.fromCharCode(chr1);

        if (enc3 != 64) {
            output = output + String.fromCharCode(chr2);
        }
        if (enc4 != 64) {
            output = output + String.fromCharCode(chr3);
        }

        chr1 = chr2 = chr3 = "";
        enc1 = enc2 = enc3 = enc4 = "";

    } while (i < input.length);

    return output;
}

(function () {
    var config_ok = true;

    // First lets make sure properties are available
    if (
        typeof(wayf_use_discovery_service) == "undefined" ||
        typeof(wayf_use_discovery_service) != "boolean"
    ) {
        wayf_use_discovery_service = true;
    }

    if (typeof(wayf_sp_entityID) == "undefined") {
        alert('The mandatory parameter \'wayf_sp_entityID\' is missing. Please add it as a javascript variable on this page.');
        config_ok = false;
    }

    if (typeof(wayf_URL) == "undefined") {
        alert('The mandatory parameter \'wayf_URL\' is missing. Please add it as a javascript variable on this page.');
        config_ok = false;
    }

    if (typeof(wayf_return_url) == "undefined") {
        alert('The mandatory parameter \'wayf_return_url\' is missing. Please add it as a javascript variable on this page.');
        config_ok = false;
    }

    if (typeof(wayf_discofeed_url) == "undefined") {
        wayf_discofeed_url = '';
    }

    if (typeof(wayf_sp_cookie_path) == "undefined") {
        wayf_sp_cookie_path = '';
    }

    if ((typeof(wayf_list_height) != "number") || (wayf_list_height < 0)) {
        wayf_list_height = '150px';
    } else {
        wayf_list_height += 'px';
    }

    if (wayf_use_discovery_service == false && typeof(wayf_sp_handlerURL) == "undefined") {
        alert('The mandatory parameter \'wayf_sp_handlerURL\' is missing. Please add it as a javascript variable on this page.');
        config_ok = false;
    }

    if (wayf_use_discovery_service == true && typeof(wayf_sp_samlDSURL) == "undefined") {
        // Set to default DS handler
        wayf_sp_samlDSURL = wayf_sp_handlerURL + "/DS";
    }

    if (typeof(wayf_sp_samlACURL) == "undefined") {
        wayf_sp_samlACURL = wayf_sp_handlerURL + '/SAML/POST';
    }

    if (typeof(wayf_font_color) == "undefined") {
        wayf_font_color = 'black';
    }

    if (
        typeof(wayf_font_size) == "undefined" ||
        typeof(wayf_font_size) != "number"
    ) {
        wayf_font_size = 12;
    }

    if (typeof(wayf_border_color) == "undefined") {
        wayf_border_color = '#00247D';
    }

    if (typeof(wayf_background_color) == "undefined") {
        wayf_background_color = '#F4F7F7';
    }

    if (
        typeof(wayf_use_small_logo) == "undefined" ||
        typeof(wayf_use_small_logo) != "boolean"
    ) {
        wayf_use_small_logo = false;
    }

    if (
        typeof(wayf_hide_logo) == "undefined" ||
        typeof(wayf_use_small_logo) != "boolean"
    ) {
        wayf_hide_logo = false;
    }

    if (typeof(wayf_width) == "undefined") {
        wayf_width = "auto";
    } else if (typeof(wayf_width) == "number") {
        wayf_width += 'px';
    }

    if (typeof(wayf_height) == "undefined") {
        wayf_height = "auto";
    } else if (typeof(wayf_height) == "number") {
        wayf_height += "px";
    }

    if (
        typeof(wayf_show_remember_checkbox) == "undefined" ||
        typeof(wayf_show_remember_checkbox) != "boolean"
    ) {
        wayf_show_remember_checkbox = true;
    }

    if (
        typeof(wayf_force_remember_for_session) == "undefined" ||
        typeof(wayf_force_remember_for_session) != "boolean"
    ) {
        wayf_force_remember_for_session = false;
    }

    if (
        typeof(wayf_auto_login) == "undefined" ||
        typeof(wayf_auto_login) != "boolean"
    ) {
        wayf_auto_login = true;
    }

    if (
        typeof(wayf_hide_after_login) == "undefined" ||
        typeof(wayf_hide_after_login) != "boolean"
    ) {
        wayf_hide_after_login = false;
    }

    if (typeof(wayf_logged_in_messsage) == "undefined") {
        wayf_logged_in_messsage = "You are already authenticated.";
    }

    if (
        typeof(wayf_most_used_idps) == "undefined" ||
        typeof(wayf_most_used_idps) != "object"
    ) {
        wayf_most_used_idps = new Array();
    }

    if (
        typeof(wayf_show_categories) == "undefined" ||
        typeof(wayf_show_categories) != "boolean"
    ) {
        wayf_show_categories = true;
    }

    if (
        typeof(wayf_hide_categories) == "undefined" ||
        typeof(wayf_hide_categories) != "object"
    ) {
        wayf_hide_categories = new Array();
    }

    if (
        typeof(wayf_unhide_idps) == "undefined" ||
        typeof(wayf_unhide_idps) != "object"
    ) {
        wayf_unhide_idps = new Array();
    }

    // Disable categories if IdPs are unhidden from hidden categories
    if (wayf_unhide_idps.length > 0) {
        wayf_show_categories = false;
    }

    if (
        typeof(wayf_hide_idps) == "undefined" ||
        typeof(wayf_hide_idps) != "object"
    ) {
        wayf_hide_idps = new Array();
    }

    if (
        typeof(wayf_additional_idps) == "undefined" ||
        typeof(wayf_additional_idps) != "object"
    ) {
        wayf_additional_idps = [];
    }

    // Exit without outputting html if config is not ok
    if (config_ok != true) {
        return;
    }

    // Check if user is logged in already:
    var user_logged_in = false;
    if (typeof(wayf_check_login_state_function) == "undefined" ||
        typeof(wayf_check_login_state_function) != "function") {
        // Use default Shibboleth Service Provider login check
        user_logged_in = isCookie('shibsession');
    } else {
        // Use custom function
        user_logged_in = wayf_check_login_state_function();
    }

    // Check if user is authenticated already and
    // whether something has to be drawn
    if (
        wayf_hide_after_login &&
        user_logged_in &&
        wayf_logged_in_messsage == ''
    ) {

        // Exit script without drawing
        return;
    }

    // Now start generating the HTML for outer box
    if (
        wayf_hide_after_login &&
        user_logged_in
    ) {
        writeHTML('<div id="wayf_div" style="background:' + wayf_background_color + ';border-style: solid;border-color: ' + wayf_border_color + ';border-width: 1px;padding: 10px;height: auto;width: ' + wayf_width + ';text-align: left;overflow: hidden;">');
    } else {
        writeHTML('<div id="wayf_div" style="background:' + wayf_background_color + ';border-style: solid;border-color: ' + wayf_border_color + ';border-width: 1px;padding: 10px;height: ' + wayf_height + ';width: ' + wayf_width + ';text-align: left;">');
    }


    // Shall we display the logo
    if (wayf_hide_logo != true) {

        // Write header of logo div
        writeHTML('<div id="wayf_logo_div" style="float: right;margin-bottom: 5px;"><a href="https://www.gakunin.jp/" target="_blank" style="border:0px">');

        // Which size of the logo shall we display
        if (wayf_use_small_logo) {
            writeHTML('<img id="wayf_logo" src="https://ds.gakunin.nii.ac.jp/GakuNinDS/images/gakunin-seal.png" alt="Federation Logo" style="border:0px">')
        } else {
            writeHTML('<img id="wayf_logo" src="https://ds.gakunin.nii.ac.jp/GakuNinDS/images/gakunin.png" alt="Federation Logo" style="border:0px">')
        }

        // Write footer of logo div
        writeHTML('</a></div>');
    }

    // Start login check
    // Search for login state cookie
    // If one exists, we only draw the logged_in_message
    if (
        wayf_hide_after_login &&
        user_logged_in
    ) {
        writeHTML('<p id="wayf_intro_div" style="float:left;font-size:' + wayf_font_size + 'px;color:' + wayf_font_color + ';">' + wayf_logged_in_messsage + '</p>');

    } else {
        // Else draw embedded WAYF

        //Do we have to draw custom text? or any text at all?
        if (typeof(wayf_overwrite_intro_text) == "undefined") {
            writeHTML('<label for="user_idp" id="wayf_intro_label" style="float:left; min-width:80px; font-size:' + wayf_font_size + 'px;color:' + wayf_font_color + ';margin-top: 5px;">Login with:');
        } else if (wayf_overwrite_intro_text != "") {
            writeHTML('<label for="user_idp" id="wayf_intro_label" style="float:left; min-width:80px; font-size:' + wayf_font_size + 'px;color:' + wayf_font_color + ';margin-top: 5px;">' + wayf_overwrite_intro_text);
        }

        // Get local cookie
        var saml_idp = getCookie('_saml_idp');
        var last_idp = '';
        var last_idps = new Array();

        if (saml_idp && saml_idp.length > 0) {
            last_idps = saml_idp.split('+')
            if (last_idps[0] && last_idps[0].length > 0) {
                last_idp = decodeBase64(last_idps[0]);
            }
        }

        if (last_idp == "" && safekind == 2) {
//            writeHTML('<img src="https://ds.gakunin.nii.ac.jp/GakuNinDS/images/alert.gif" id="icon-alert" title="Alert SP!" style="vertical-align:text-bottom; border:0px; width:20px; height:20px;">');
        }
        writeHTML('</label>');

        var wayf_authReq_URL = '';
        var form_start = '';

        if (wayf_use_discovery_service == true) {
            var return_url = wayf_sp_samlDSURL + (wayf_sp_samlDSURL.indexOf('?') >= 0 ? '&' : '?') + 'SAMLDS=1&target=' + encodeURIComponent(wayf_return_url);

            wayf_authReq_URL = wayf_URL +
                '?entityID=' + encodeURIComponent(wayf_sp_entityID) +
                '&amp;return=' + encodeURIComponent(return_url);

            form_start = '<form id="IdPList" name="IdPList" method="post" target="_parent" onSubmit="return submitForm()" action="' + wayf_authReq_URL + '">';
        } else {

            wayf_authReq_URL = wayf_URL +
                '?providerId=' + encodeURIComponent(wayf_sp_entityID) +
                '&amp;shire=' + encodeURIComponent(wayf_sp_samlACURL) +
                '&amp;target=' + encodeURIComponent(wayf_return_url);

            form_start = '<form id="IdPList" name="IdPList" method="post" target="_parent" onSubmit="return submitForm()" action="' + wayf_authReq_URL + '&amp;time=1583392121' +
                '">';
        }

        writeHTML('<link rel="stylesheet" href="https://ds.gakunin.nii.ac.jp/GakuNinDS/incsearch/suggest.css" type="text/css" />');
        writeHTML('<script type="text/javascript" src="https://ds.gakunin.nii.ac.jp/GakuNinDS/incsearch/jquery.js"></script>');
        writeHTML('<script type="text/javascript" src="https://ds.gakunin.nii.ac.jp/GakuNinDS/incsearch/jquery.flickable.js"></script>');
        writeHTML('<script type="text/javascript" src="https://ds.gakunin.nii.ac.jp/GakuNinDS/incsearch/suggest.js"></script>');

        writeHTML(form_start);
        writeHTML('<input name="request_type" type="hidden" value="embedded">');
        writeHTML('<input id="user_idp" name="user_idp" type="hidden" value="">');

        // Favourites
        if (wayf_most_used_idps.length > 0) {
            if (typeof(wayf_overwrite_most_used_idps_text) != "undefined") {
                favorite_idp_group = wayf_overwrite_most_used_idps_text;
            }

            // Show additional IdPs in the order they are defined
            for (var i = 0; i < wayf_most_used_idps.length; i++) {
                if (wayf_idps[wayf_most_used_idps[i]]) {
                    favorite_list.push(wayf_idps[wayf_most_used_idps[i]].search.slice());
                    favorite_list[favorite_list.length - 1][1] = favorite_idp_group;
                }
            }
        }
        if (last_idp == 'https://shib-idp01.iic.hokudai.ac.jp/idp/shibboleth') {
            dispDefault = 'Hokkaido University';
        }
        if (isAllowedType('https://shib-idp01.iic.hokudai.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://shib-idp01.iic.hokudai.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shib-idp01.iic.hokudai.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Hokkaido University';
            }
            pushIncSearchList('https://shib-idp01.iic.hokudai.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.asahikawa-med.ac.jp/idp/shibboleth') {
            dispDefault = 'Asahikawa Medical University';
        }
        if (isAllowedType('https://idp.asahikawa-med.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://idp.asahikawa-med.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.asahikawa-med.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Asahikawa Medical University';
            }
            pushIncSearchList('https://idp.asahikawa-med.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.msls.kushiro-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Kushiro College';
        }
        if (isAllowedType('https://idp.msls.kushiro-ct.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://idp.msls.kushiro-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.msls.kushiro-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Kushiro College';
            }
            pushIncSearchList('https://idp.msls.kushiro-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shibboleth.lib.kitami-it.ac.jp/idp/shibboleth') {
            dispDefault = 'Kitami Institute of Technology';
        }
        if (isAllowedType('https://shibboleth.lib.kitami-it.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://shibboleth.lib.kitami-it.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shibboleth.lib.kitami-it.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kitami Institute of Technology';
            }
            pushIncSearchList('https://shibboleth.lib.kitami-it.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://sso.sapmed.ac.jp/idp/shibboleth') {
            dispDefault = 'Sapporo Medical University';
        }
        if (isAllowedType('https://sso.sapmed.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://sso.sapmed.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://sso.sapmed.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Sapporo Medical University';
            }
            pushIncSearchList('https://sso.sapmed.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.tomakomai-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Tomakomai College';
        }
        if (isAllowedType('https://kidp.tomakomai-ct.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://kidp.tomakomai-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.tomakomai-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Tomakomai College';
            }
            pushIncSearchList('https://kidp.tomakomai-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.hakodate-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Hakodate College';
        }
        if (isAllowedType('https://kidp.hakodate-ct.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://kidp.hakodate-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.hakodate-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Hakodate College';
            }
            pushIncSearchList('https://kidp.hakodate-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.asahikawa-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Asahikawa College';
        }
        if (isAllowedType('https://kidp.asahikawa-nct.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://kidp.asahikawa-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.asahikawa-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Asahikawa College';
            }
            pushIncSearchList('https://kidp.asahikawa-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.sgu.ac.jp/idp/shibboleth') {
            dispDefault = 'Sapporo Gakuin University';
        }
        if (isAllowedType('https://idp.sgu.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://idp.sgu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.sgu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Sapporo Gakuin University';
            }
            pushIncSearchList('https://idp.sgu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin-idp01.mmm.muroran-it.ac.jp/idp/shibboleth') {
            dispDefault = 'Muroran Institute of Technology';
        }
        if (isAllowedType('https://gakunin-idp01.mmm.muroran-it.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://gakunin-idp01.mmm.muroran-it.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin-idp01.mmm.muroran-it.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Muroran Institute of Technology';
            }
            pushIncSearchList('https://gakunin-idp01.mmm.muroran-it.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.fun.ac.jp/idp/shibboleth') {
            dispDefault = 'Future University Hakodate';
        }
        if (isAllowedType('https://idp.fun.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://idp.fun.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.fun.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Future University Hakodate';
            }
            pushIncSearchList('https://idp.fun.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.hokkyodai.ac.jp/idp/shibboleth') {
            dispDefault = 'Hokkaido University of Education';
        }
        if (isAllowedType('https://idp.hokkyodai.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://idp.hokkyodai.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.hokkyodai.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Hokkaido University of Education';
            }
            pushIncSearchList('https://idp.hokkyodai.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://sib-idp.obihiro.ac.jp/idp/shibboleth') {
            dispDefault = 'Obihiro University of Agriculture and Veterinary Medicine';
        }
        if (isAllowedType('https://sib-idp.obihiro.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://sib-idp.obihiro.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://sib-idp.obihiro.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Obihiro University of Agriculture and Veterinary Medicine';
            }
            pushIncSearchList('https://sib-idp.obihiro.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.scu.ac.jp/idp/shibboleth') {
            dispDefault = 'Sapporo City University';
        }
        if (isAllowedType('https://idp.scu.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://idp.scu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.scu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Sapporo City University';
            }
            pushIncSearchList('https://idp.scu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://rg-lshib01.rakuno.ac.jp/idp/shibboleth') {
            dispDefault = 'RAKUNO GAKUEN UNIVERSITY';
        }
        if (isAllowedType('https://rg-lshib01.rakuno.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://rg-lshib01.rakuno.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://rg-lshib01.rakuno.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'RAKUNO GAKUEN UNIVERSITY';
            }
            pushIncSearchList('https://rg-lshib01.rakuno.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://ictc-idp01.otaru-uc.ac.jp/idp/shibboleth') {
            dispDefault = 'Otaru University of Commerce';
        }
        if (isAllowedType('https://ictc-idp01.otaru-uc.ac.jp/idp/shibboleth', 'hokkaido') && isAllowedIdP('https://ictc-idp01.otaru-uc.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://ictc-idp01.otaru-uc.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Otaru University of Commerce';
            }
            pushIncSearchList('https://ictc-idp01.otaru-uc.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://upki.yamagata-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Yamagata University';
        }
        if (isAllowedType('https://upki.yamagata-u.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://upki.yamagata-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://upki.yamagata-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Yamagata University';
            }
            pushIncSearchList('https://upki.yamagata-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.miyakyo-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Miyagi University of Education';
        }
        if (isAllowedType('https://idp.miyakyo-u.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://idp.miyakyo-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.miyakyo-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Miyagi University of Education';
            }
            pushIncSearchList('https://idp.miyakyo-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.ichinoseki.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Ichinoseki College';
        }
        if (isAllowedType('https://kidp.ichinoseki.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://kidp.ichinoseki.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.ichinoseki.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Ichinoseki College';
            }
            pushIncSearchList('https://kidp.ichinoseki.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.hachinohe-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Hachinohe College';
        }
        if (isAllowedType('https://kidp.hachinohe-ct.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://kidp.hachinohe-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.hachinohe-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Hachinohe College';
            }
            pushIncSearchList('https://kidp.hachinohe-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://ksidp.sendai-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Sendai College,Hirose';
        }
        if (isAllowedType('https://ksidp.sendai-nct.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://ksidp.sendai-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://ksidp.sendai-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Sendai College,Hirose';
            }
            pushIncSearchList('https://ksidp.sendai-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.akita-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Akita College';
        }
        if (isAllowedType('https://kidp.akita-nct.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://kidp.akita-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.akita-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Akita College';
            }
            pushIncSearchList('https://kidp.akita-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.auth.tohoku.ac.jp/idp/shibboleth') {
            dispDefault = 'Tohoku University';
        }
        if (isAllowedType('https://idp.auth.tohoku.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://idp.auth.tohoku.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.auth.tohoku.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tohoku University';
            }
            pushIncSearchList('https://idp.auth.tohoku.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.tsuruoka-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Tsuruoka College';
        }
        if (isAllowedType('https://kidp.tsuruoka-nct.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://kidp.tsuruoka-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.tsuruoka-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Tsuruoka College';
            }
            pushIncSearchList('https://kidp.tsuruoka-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.fukushima-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Fukushima College';
        }
        if (isAllowedType('https://kidp.fukushima-nct.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://kidp.fukushima-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.fukushima-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Fukushima College';
            }
            pushIncSearchList('https://kidp.fukushima-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://knidp.sendai-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Sendai College,Natori';
        }
        if (isAllowedType('https://knidp.sendai-nct.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://knidp.sendai-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://knidp.sendai-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Sendai College,Natori';
            }
            pushIncSearchList('https://knidp.sendai-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.tohtech.ac.jp/idp/shibboleth') {
            dispDefault = 'Tohoku Institute of Technology';
        }
        if (isAllowedType('https://idp.tohtech.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://idp.tohtech.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.tohtech.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tohoku Institute of Technology';
            }
            pushIncSearchList('https://idp.tohtech.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://auas.akita-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Akita University';
        }
        if (isAllowedType('https://auas.akita-u.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://auas.akita-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://auas.akita-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Akita University';
            }
            pushIncSearchList('https://auas.akita-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp01.gn.hirosaki-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Hirosaki University';
        }
        if (isAllowedType('https://idp01.gn.hirosaki-u.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://idp01.gn.hirosaki-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp01.gn.hirosaki-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Hirosaki University';
            }
            pushIncSearchList('https://idp01.gn.hirosaki-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.u-aizu.ac.jp/idp/shibboleth') {
            dispDefault = 'The University of Aizu';
        }
        if (isAllowedType('https://idp.u-aizu.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://idp.u-aizu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.u-aizu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'The University of Aizu';
            }
            pushIncSearchList('https://idp.u-aizu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://axl.aiu.ac.jp/idp/shibboleth') {
            dispDefault = 'Akita International University';
        }
        if (isAllowedType('https://axl.aiu.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://axl.aiu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://axl.aiu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Akita International University';
            }
            pushIncSearchList('https://axl.aiu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.fmu.ac.jp/idp/shibboleth') {
            dispDefault = 'Fukushima Medical University';
        }
        if (isAllowedType('https://idp.fmu.ac.jp/idp/shibboleth', 'tohoku') && isAllowedIdP('https://idp.fmu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.fmu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Fukushima Medical University';
            }
            pushIncSearchList('https://idp.fmu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://tg.ex-tic.com/auth/gakunin/saml2/assertions') {
            dispDefault = 'Tohoku Gakuin University';
        }
        if (isAllowedType('https://tg.ex-tic.com/auth/gakunin/saml2/assertions', 'tohoku') && isAllowedIdP('https://tg.ex-tic.com/auth/gakunin/saml2/assertions')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://tg.ex-tic.com/auth/gakunin/saml2/assertions"
            ) {
                dispDefault = 'Tohoku Gakuin University';
            }
            pushIncSearchList('https://tg.ex-tic.com/auth/gakunin/saml2/assertions');
        }
        if (last_idp == 'https://idp.nii.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Informatics';
        }
        if (isAllowedType('https://idp.nii.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.nii.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.nii.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Informatics';
            }
            pushIncSearchList('https://idp.nii.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://upki-idp.chiba-u.jp/idp/shibboleth') {
            dispDefault = 'Chiba University';
        }
        if (isAllowedType('https://upki-idp.chiba-u.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://upki-idp.chiba-u.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://upki-idp.chiba-u.jp/idp/shibboleth"
            ) {
                dispDefault = 'Chiba University';
            }
            pushIncSearchList('https://upki-idp.chiba-u.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.account.tsukuba.ac.jp/idp/shibboleth') {
            dispDefault = 'University of Tsukuba';
        }
        if (isAllowedType('https://idp.account.tsukuba.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.account.tsukuba.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.account.tsukuba.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'University of Tsukuba';
            }
            pushIncSearchList('https://idp.account.tsukuba.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://asura.seijo.ac.jp/idp/shibboleth') {
            dispDefault = 'Seijo University';
        }
        if (isAllowedType('https://asura.seijo.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://asura.seijo.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://asura.seijo.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Seijo University';
            }
            pushIncSearchList('https://asura.seijo.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://upki.toho-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Toho University';
        }
        if (isAllowedType('https://upki.toho-u.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://upki.toho-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://upki.toho-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Toho University';
            }
            pushIncSearchList('https://upki.toho-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shibboleth.nihon-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Nihon University';
        }
        if (isAllowedType('https://shibboleth.nihon-u.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://shibboleth.nihon-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shibboleth.nihon-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Nihon University';
            }
            pushIncSearchList('https://shibboleth.nihon-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://upki-idp.rikkyo.ac.jp/idp/shibboleth') {
            dispDefault = 'Rikkyo University';
        }
        if (isAllowedType('https://upki-idp.rikkyo.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://upki-idp.rikkyo.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://upki-idp.rikkyo.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Rikkyo University';
            }
            pushIncSearchList('https://upki-idp.rikkyo.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://servs.lib.meiji.ac.jp/idp/shibboleth') {
            dispDefault = 'Meiji University';
        }
        if (isAllowedType('https://servs.lib.meiji.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://servs.lib.meiji.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://servs.lib.meiji.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Meiji University';
            }
            pushIncSearchList('https://servs.lib.meiji.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://ws1.jichi.ac.jp/idp/shibboleth') {
            dispDefault = 'Jichi Medical University(old)';
        }
        if (isAllowedType('https://ws1.jichi.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://ws1.jichi.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://ws1.jichi.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Jichi Medical University(old)';
            }
            pushIncSearchList('https://ws1.jichi.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin-idp.ynu.ac.jp/') {
            dispDefault = 'Yokohama National University';
        }
        if (isAllowedType('https://gakunin-idp.ynu.ac.jp/', 'kanto') && isAllowedIdP('https://gakunin-idp.ynu.ac.jp/')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin-idp.ynu.ac.jp/"
            ) {
                dispDefault = 'Yokohama National University';
            }
            pushIncSearchList('https://gakunin-idp.ynu.ac.jp/');
        }
        if (last_idp == 'https://saml-2.tmd.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo Medical and Dental University';
        }
        if (isAllowedType('https://saml-2.tmd.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://saml-2.tmd.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://saml-2.tmd.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo Medical and Dental University';
            }
            pushIncSearchList('https://saml-2.tmd.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.kosen-k.go.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology';
        }
        if (isAllowedType('https://kidp.kosen-k.go.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://kidp.kosen-k.go.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.kosen-k.go.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology';
            }
            pushIncSearchList('https://kidp.kosen-k.go.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.tdc.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo Dental College';
        }
        if (isAllowedType('https://idp.tdc.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.tdc.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.tdc.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo Dental College';
            }
            pushIncSearchList('https://idp.tdc.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shib.ap.showa-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Showa University';
        }
        if (isAllowedType('https://shib.ap.showa-u.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://shib.ap.showa-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shib.ap.showa-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Showa University';
            }
            pushIncSearchList('https://shib.ap.showa-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://ill.lib.kth.isp.ntt-east.co.jp/idp/shibboleth') {
            dispDefault = 'NTT Medical Center Tokyo';
        }
        if (isAllowedType('https://ill.lib.kth.isp.ntt-east.co.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://ill.lib.kth.isp.ntt-east.co.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://ill.lib.kth.isp.ntt-east.co.jp/idp/shibboleth"
            ) {
                dispDefault = 'NTT Medical Center Tokyo';
            }
            pushIncSearchList('https://ill.lib.kth.isp.ntt-east.co.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp01.ipc.kaiyodai.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo University of Marine Science and Technology';
        }
        if (isAllowedType('https://idp01.ipc.kaiyodai.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp01.ipc.kaiyodai.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp01.ipc.kaiyodai.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo University of Marine Science and Technology';
            }
            pushIncSearchList('https://idp01.ipc.kaiyodai.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.soka.ac.jp/idp/shibboleth') {
            dispDefault = 'Soka University';
        }
        if (isAllowedType('https://idp.soka.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.soka.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.soka.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Soka University';
            }
            pushIncSearchList('https://idp.soka.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.igakuken.or.jp/idp/shibboleth') {
            dispDefault = 'Tokyo Metropolitan Institute of Medical Science';
        }
        if (isAllowedType('https://idp.igakuken.or.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.igakuken.or.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.igakuken.or.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo Metropolitan Institute of Medical Science';
            }
            pushIncSearchList('https://idp.igakuken.or.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakuninidp.sic.shibaura-it.ac.jp/idp/shibboleth') {
            dispDefault = 'Shibaura Institute of Technology';
        }
        if (isAllowedType('https://gakuninidp.sic.shibaura-it.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://gakuninidp.sic.shibaura-it.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakuninidp.sic.shibaura-it.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Shibaura Institute of Technology';
            }
            pushIncSearchList('https://gakuninidp.sic.shibaura-it.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://tgu.u-gakugei.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo Gakugei University';
        }
        if (isAllowedType('https://tgu.u-gakugei.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://tgu.u-gakugei.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://tgu.u-gakugei.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo Gakugei University';
            }
            pushIncSearchList('https://tgu.u-gakugei.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.musashi.ac.jp/idp/shibboleth') {
            dispDefault = 'Musashi Academy';
        }
        if (isAllowedType('https://idp.musashi.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.musashi.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.musashi.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Musashi Academy';
            }
            pushIncSearchList('https://idp.musashi.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.it-chiba.ac.jp/idp/shibboleth') {
            dispDefault = 'Chiba Institute of Technology';
        }
        if (isAllowedType('https://idp.it-chiba.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.it-chiba.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.it-chiba.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Chiba Institute of Technology';
            }
            pushIncSearchList('https://idp.it-chiba.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shibboleth.tama.ac.jp/idp/shibboleth') {
            dispDefault = 'Tama University';
        }
        if (isAllowedType('https://shibboleth.tama.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://shibboleth.tama.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shibboleth.tama.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tama University';
            }
            pushIncSearchList('https://shibboleth.tama.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://upkishib.cc.ocha.ac.jp/idp/shibboleth') {
            dispDefault = 'Ochanomizu University';
        }
        if (isAllowedType('https://upkishib.cc.ocha.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://upkishib.cc.ocha.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://upkishib.cc.ocha.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Ochanomizu University';
            }
            pushIncSearchList('https://upkishib.cc.ocha.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.tokyo-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Tokyo College';
        }
        if (isAllowedType('https://kidp.tokyo-ct.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://kidp.tokyo-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.tokyo-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Tokyo College';
            }
            pushIncSearchList('https://kidp.tokyo-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.gunma-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Gunma University';
        }
        if (isAllowedType('https://idp.gunma-u.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.gunma-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.gunma-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Gunma University';
            }
            pushIncSearchList('https://idp.gunma-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.oyama-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Oyama College';
        }
        if (isAllowedType('https://kidp.oyama-ct.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://kidp.oyama-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.oyama-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Oyama College';
            }
            pushIncSearchList('https://kidp.oyama-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin1.keio.ac.jp/idp/shibboleth') {
            dispDefault = 'Keio University';
        }
        if (isAllowedType('https://gakunin1.keio.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://gakunin1.keio.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin1.keio.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Keio University';
            }
            pushIncSearchList('https://gakunin1.keio.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.gunma-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Gunma College';
        }
        if (isAllowedType('https://kidp.gunma-ct.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://kidp.gunma-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.gunma-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Gunma College';
            }
            pushIncSearchList('https://kidp.gunma-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shibboleth-idp.dokkyomed.ac.jp/idp/shibboleth') {
            dispDefault = 'Dokkyo Medical University';
        }
        if (isAllowedType('https://shibboleth-idp.dokkyomed.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://shibboleth-idp.dokkyomed.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shibboleth-idp.dokkyomed.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Dokkyo Medical University';
            }
            pushIncSearchList('https://shibboleth-idp.dokkyomed.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://iccoam.tufs.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo University of Foreign Studies';
        }
        if (isAllowedType('https://iccoam.tufs.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://iccoam.tufs.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://iccoam.tufs.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo University of Foreign Studies';
            }
            pushIncSearchList('https://iccoam.tufs.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.ibaraki-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Ibaraki College';
        }
        if (isAllowedType('https://kidp.ibaraki-ct.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://kidp.ibaraki-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.ibaraki-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Ibaraki College';
            }
            pushIncSearchList('https://kidp.ibaraki-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shibboleth.cc.uec.ac.jp/idp/shibboleth') {
            dispDefault = 'The University of Electro-Communications';
        }
        if (isAllowedType('https://shibboleth.cc.uec.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://shibboleth.cc.uec.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shibboleth.cc.uec.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'The University of Electro-Communications';
            }
            pushIncSearchList('https://shibboleth.cc.uec.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.sys.affrc.go.jp/idp/shibboleth') {
            dispDefault = 'AFFRIT/MAFFIN';
        }
        if (isAllowedType('https://idp.sys.affrc.go.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.sys.affrc.go.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.sys.affrc.go.jp/idp/shibboleth"
            ) {
                dispDefault = 'AFFRIT/MAFFIN';
            }
            pushIncSearchList('https://idp.sys.affrc.go.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.kisarazu.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Kisarazu College';
        }
        if (isAllowedType('https://kidp.kisarazu.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://kidp.kisarazu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.kisarazu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Kisarazu College';
            }
            pushIncSearchList('https://kidp.kisarazu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin-idp.c.chuo-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Chuo University';
        }
        if (isAllowedType('https://gakunin-idp.c.chuo-u.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://gakunin-idp.c.chuo-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin-idp.c.chuo-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Chuo University';
            }
            pushIncSearchList('https://gakunin-idp.c.chuo-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gidp.adm.u-tokyo.ac.jp/idp/shibboleth') {
            dispDefault = 'The University of Tokyo';
        }
        if (isAllowedType('https://gidp.adm.u-tokyo.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://gidp.adm.u-tokyo.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gidp.adm.u-tokyo.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'The University of Tokyo';
            }
            pushIncSearchList('https://gidp.adm.u-tokyo.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.dendai.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo Denki University';
        }
        if (isAllowedType('https://idp.dendai.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.dendai.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.dendai.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo Denki University';
            }
            pushIncSearchList('https://idp.dendai.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.cc.seikei.ac.jp/idp/shibboleth') {
            dispDefault = 'Seikei University';
        }
        if (isAllowedType('https://idp.cc.seikei.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.cc.seikei.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.cc.seikei.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Seikei University';
            }
            pushIncSearchList('https://idp.cc.seikei.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.teikyo-u.ac.jp/AccessManager/shibboleth') {
            dispDefault = 'Teikyo University';
        }
        if (isAllowedType('https://idp.teikyo-u.ac.jp/AccessManager/shibboleth', 'kanto') && isAllowedIdP('https://idp.teikyo-u.ac.jp/AccessManager/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.teikyo-u.ac.jp/AccessManager/shibboleth"
            ) {
                dispDefault = 'Teikyo University';
            }
            pushIncSearchList('https://idp.teikyo-u.ac.jp/AccessManager/shibboleth');
        }
        if (last_idp == 'https://idp.tau.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo Ariake University of Medical and Health Sciences';
        }
        if (isAllowedType('https://idp.tau.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.tau.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.tau.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo Ariake University of Medical and Health Sciences';
            }
            pushIncSearchList('https://idp.tau.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.tokyo-kasei.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo Kasei University';
        }
        if (isAllowedType('https://idp.tokyo-kasei.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.tokyo-kasei.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.tokyo-kasei.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo Kasei University';
            }
            pushIncSearchList('https://idp.tokyo-kasei.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.grips.ac.jp/idp/shibboleth') {
            dispDefault = 'National Graduate Institute for Policy Studies';
        }
        if (isAllowedType('https://idp.grips.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.grips.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.grips.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Graduate Institute for Policy Studies';
            }
            pushIncSearchList('https://idp.grips.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakuninshib.tmu.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo Metropolitan University';
        }
        if (isAllowedType('https://gakuninshib.tmu.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://gakuninshib.tmu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakuninshib.tmu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo Metropolitan University';
            }
            pushIncSearchList('https://gakuninshib.tmu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp-gakunin.nap.gsic.titech.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo Institute of Technology';
        }
        if (isAllowedType('https://idp-gakunin.nap.gsic.titech.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp-gakunin.nap.gsic.titech.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp-gakunin.nap.gsic.titech.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo Institute of Technology';
            }
            pushIncSearchList('https://idp-gakunin.nap.gsic.titech.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.tsurumi-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Tsurumi University';
        }
        if (isAllowedType('https://idp.tsurumi-u.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.tsurumi-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.tsurumi-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tsurumi University';
            }
            pushIncSearchList('https://idp.tsurumi-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://sidp.ibaraki.ac.jp/idp/shibboleth') {
            dispDefault = 'Ibaraki University';
        }
        if (isAllowedType('https://sidp.ibaraki.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://sidp.ibaraki.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://sidp.ibaraki.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Ibaraki University';
            }
            pushIncSearchList('https://sidp.ibaraki.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.nims.go.jp/idp/shibboleth') {
            dispDefault = 'National Institute for Materials Science';
        }
        if (isAllowedType('https://idp.nims.go.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.nims.go.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.nims.go.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute for Materials Science';
            }
            pushIncSearchList('https://idp.nims.go.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.toyaku.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo University of Pharmacy and Life Sciences';
        }
        if (isAllowedType('https://idp.toyaku.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.toyaku.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.toyaku.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo University of Pharmacy and Life Sciences';
            }
            pushIncSearchList('https://idp.toyaku.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin2.tuat.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo University of Agriculture and Technology';
        }
        if (isAllowedType('https://gakunin2.tuat.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://gakunin2.tuat.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin2.tuat.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo University of Agriculture and Technology';
            }
            pushIncSearchList('https://gakunin2.tuat.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin-idp.shodai.ac.jp/idp/shibboleth') {
            dispDefault = 'Yokohama College of Commerce';
        }
        if (isAllowedType('https://gakunin-idp.shodai.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://gakunin-idp.shodai.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin-idp.shodai.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Yokohama College of Commerce';
            }
            pushIncSearchList('https://gakunin-idp.shodai.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://koma-sso.komazawa-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Komazawa University';
        }
        if (isAllowedType('https://koma-sso.komazawa-u.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://koma-sso.komazawa-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://koma-sso.komazawa-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Komazawa University';
            }
            pushIncSearchList('https://koma-sso.komazawa-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp3.qst.go.jp/idp/shibboleth') {
            dispDefault = 'National Institutes for Quantum and Radiological Science and Technology';
        }
        if (isAllowedType('https://idp3.qst.go.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp3.qst.go.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp3.qst.go.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institutes for Quantum and Radiological Science and Technology';
            }
            pushIncSearchList('https://idp3.qst.go.jp/idp/shibboleth');
        }
        if (last_idp == 'https://rprx.rku.ac.jp/idp/shibboleth') {
            dispDefault = 'Ryutsu Keizai University';
        }
        if (isAllowedType('https://rprx.rku.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://rprx.rku.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://rprx.rku.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Ryutsu Keizai University';
            }
            pushIncSearchList('https://rprx.rku.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.kanagawa-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kanagawa University';
        }
        if (isAllowedType('https://idp.kanagawa-u.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.kanagawa-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.kanagawa-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kanagawa University';
            }
            pushIncSearchList('https://idp.kanagawa-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.ide.go.jp/idp/shibboleth') {
            dispDefault = 'IDE-JETRO';
        }
        if (isAllowedType('https://idp.ide.go.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.ide.go.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.ide.go.jp/idp/shibboleth"
            ) {
                dispDefault = 'IDE-JETRO';
            }
            pushIncSearchList('https://idp.ide.go.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.senshu-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Senshu University';
        }
        if (isAllowedType('https://idp.senshu-u.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.senshu-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.senshu-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Senshu University';
            }
            pushIncSearchList('https://idp.senshu-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.geidai.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokyo University of the Arts';
        }
        if (isAllowedType('https://idp.geidai.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.geidai.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.geidai.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokyo University of the Arts';
            }
            pushIncSearchList('https://idp.geidai.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.aoyama.ac.jp/idp/shibboleth') {
            dispDefault = 'Aoyama Gakuin University';
        }
        if (isAllowedType('https://idp.aoyama.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.aoyama.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.aoyama.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Aoyama Gakuin University';
            }
            pushIncSearchList('https://idp.aoyama.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://sso.internet.ac.jp') {
            dispDefault = 'Tokyo Online University';
        }
        if (isAllowedType('https://sso.internet.ac.jp', 'kanto') && isAllowedIdP('https://sso.internet.ac.jp')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://sso.internet.ac.jp"
            ) {
                dispDefault = 'Tokyo Online University';
            }
            pushIncSearchList('https://sso.internet.ac.jp');
        }
        if (last_idp == 'https://idp.itc.saitama-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Saitama University';
        }
        if (isAllowedType('https://idp.itc.saitama-u.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.itc.saitama-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.itc.saitama-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Saitama University';
            }
            pushIncSearchList('https://idp.itc.saitama-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://lib.nmct.ntt-east.co.jp/idp/shibboleth') {
            dispDefault = 'NTT Medical Center Tokyo Library';
        }
        if (isAllowedType('https://lib.nmct.ntt-east.co.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://lib.nmct.ntt-east.co.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://lib.nmct.ntt-east.co.jp/idp/shibboleth"
            ) {
                dispDefault = 'NTT Medical Center Tokyo Library';
            }
            pushIncSearchList('https://lib.nmct.ntt-east.co.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.my-pharm.ac.jp/idp/shibboleth') {
            dispDefault = 'Meiji Pharmaceutical University';
        }
        if (isAllowedType('https://idp.my-pharm.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.my-pharm.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.my-pharm.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Meiji Pharmaceutical University';
            }
            pushIncSearchList('https://idp.my-pharm.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin.st.daito.ac.jp/idp/shibboleth') {
            dispDefault = 'Daito Bunka University';
        }
        if (isAllowedType('https://gakunin.st.daito.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://gakunin.st.daito.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin.st.daito.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Daito Bunka University';
            }
            pushIncSearchList('https://gakunin.st.daito.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.kiryu-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kiryu University';
        }
        if (isAllowedType('https://idp.kiryu-u.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.kiryu-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.kiryu-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kiryu University';
            }
            pushIncSearchList('https://idp.kiryu-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://slink.secioss.com/icu.ac.jp') {
            dispDefault = 'International Christian University';
        }
        if (isAllowedType('https://slink.secioss.com/icu.ac.jp', 'kanto') && isAllowedIdP('https://slink.secioss.com/icu.ac.jp')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://slink.secioss.com/icu.ac.jp"
            ) {
                dispDefault = 'International Christian University';
            }
            pushIncSearchList('https://slink.secioss.com/icu.ac.jp');
        }
        if (last_idp == 'https://iaidp.ia.waseda.jp/idp/shibboleth') {
            dispDefault = 'Waseda University';
        }
        if (isAllowedType('https://iaidp.ia.waseda.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://iaidp.ia.waseda.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://iaidp.ia.waseda.jp/idp/shibboleth"
            ) {
                dispDefault = 'Waseda University';
            }
            pushIncSearchList('https://iaidp.ia.waseda.jp/idp/shibboleth');
        }
        if (last_idp == 'https://sh-idp.riken.jp/idp/shibboleth') {
            dispDefault = 'RIKEN';
        }
        if (isAllowedType('https://sh-idp.riken.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://sh-idp.riken.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://sh-idp.riken.jp/idp/shibboleth"
            ) {
                dispDefault = 'RIKEN';
            }
            pushIncSearchList('https://sh-idp.riken.jp/idp/shibboleth');
        }
        if (last_idp == 'https://obirin.ex-tic.com/auth/gakunin/saml2/assertions') {
            dispDefault = 'J. F. Oberlin University';
        }
        if (isAllowedType('https://obirin.ex-tic.com/auth/gakunin/saml2/assertions', 'kanto') && isAllowedIdP('https://obirin.ex-tic.com/auth/gakunin/saml2/assertions')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://obirin.ex-tic.com/auth/gakunin/saml2/assertions"
            ) {
                dispDefault = 'J. F. Oberlin University';
            }
            pushIncSearchList('https://obirin.ex-tic.com/auth/gakunin/saml2/assertions');
        }
        if (last_idp == 'https://idp.jichi.ac.jp/idp/shibboleth') {
            dispDefault = 'Jichi Medical University';
        }
        if (isAllowedType('https://idp.jichi.ac.jp/idp/shibboleth', 'kanto') && isAllowedIdP('https://idp.jichi.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.jichi.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Jichi Medical University';
            }
            pushIncSearchList('https://idp.jichi.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://fed.mie-u.ac.jp/idp') {
            dispDefault = 'Mie University';
        }
        if (isAllowedType('https://fed.mie-u.ac.jp/idp', 'chubu') && isAllowedIdP('https://fed.mie-u.ac.jp/idp')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://fed.mie-u.ac.jp/idp"
            ) {
                dispDefault = 'Mie University';
            }
            pushIncSearchList('https://fed.mie-u.ac.jp/idp');
        }
        if (last_idp == 'https://gakunin.ealps.shinshu-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Shinshu University';
        }
        if (isAllowedType('https://gakunin.ealps.shinshu-u.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://gakunin.ealps.shinshu-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin.ealps.shinshu-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Shinshu University';
            }
            pushIncSearchList('https://gakunin.ealps.shinshu-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gknidp.ict.nitech.ac.jp/idp/shibboleth') {
            dispDefault = 'Nagoya Institute of Technology';
        }
        if (isAllowedType('https://gknidp.ict.nitech.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://gknidp.ict.nitech.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gknidp.ict.nitech.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Nagoya Institute of Technology';
            }
            pushIncSearchList('https://gknidp.ict.nitech.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.yamanashi.ac.jp/idp/shibboleth') {
            dispDefault = 'University of Yamanashi';
        }
        if (isAllowedType('https://idp.yamanashi.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp.yamanashi.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.yamanashi.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'University of Yamanashi';
            }
            pushIncSearchList('https://idp.yamanashi.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.suzuka-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Suzuka College';
        }
        if (isAllowedType('https://idp.suzuka-ct.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp.suzuka-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.suzuka-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Suzuka College';
            }
            pushIncSearchList('https://idp.suzuka-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.imc.tut.ac.jp/idp/shibboleth') {
            dispDefault = 'Toyohashi University of Technology';
        }
        if (isAllowedType('https://idp.imc.tut.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp.imc.tut.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.imc.tut.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Toyohashi University of Technology';
            }
            pushIncSearchList('https://idp.imc.tut.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.fukui-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Fukui College';
        }
        if (isAllowedType('https://kidp.fukui-nct.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://kidp.fukui-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.fukui-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Fukui College';
            }
            pushIncSearchList('https://kidp.fukui-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.shizuoka.ac.jp/idp/shibboleth') {
            dispDefault = 'Shizuoka University';
        }
        if (isAllowedType('https://idp.shizuoka.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp.shizuoka.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.shizuoka.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Shizuoka University';
            }
            pushIncSearchList('https://idp.shizuoka.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://wagner.isc.chubu.ac.jp/idp/shibboleth') {
            dispDefault = 'CHUBU UNIVERSITY';
        }
        if (isAllowedType('https://wagner.isc.chubu.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://wagner.isc.chubu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://wagner.isc.chubu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'CHUBU UNIVERSITY';
            }
            pushIncSearchList('https://wagner.isc.chubu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.nagaoka-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Nagaoka College';
        }
        if (isAllowedType('https://kidp.nagaoka-ct.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://kidp.nagaoka-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.nagaoka-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Nagaoka College';
            }
            pushIncSearchList('https://kidp.nagaoka-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.numazu-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Numazu College';
        }
        if (isAllowedType('https://kidp.numazu-ct.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://kidp.numazu-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.numazu-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Numazu College';
            }
            pushIncSearchList('https://kidp.numazu-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.nagano-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Nagano College';
        }
        if (isAllowedType('https://kidp.nagano-nct.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://kidp.nagano-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.nagano-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Nagano College';
            }
            pushIncSearchList('https://kidp.nagano-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.ishikawa-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Ishikawa College';
        }
        if (isAllowedType('https://kidp.ishikawa-nct.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://kidp.ishikawa-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.ishikawa-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Ishikawa College';
            }
            pushIncSearchList('https://kidp.ishikawa-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kiidp.nc-toyama.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Toyama College';
        }
        if (isAllowedType('https://kiidp.nc-toyama.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://kiidp.nc-toyama.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kiidp.nc-toyama.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Toyama College';
            }
            pushIncSearchList('https://kiidp.nc-toyama.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.toba-cmt.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Toba College';
        }
        if (isAllowedType('https://kidp.toba-cmt.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://kidp.toba-cmt.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.toba-cmt.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Toba College';
            }
            pushIncSearchList('https://kidp.toba-cmt.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.gifu-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Gifu College';
        }
        if (isAllowedType('https://kidp.gifu-nct.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://kidp.gifu-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.gifu-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Gifu College';
            }
            pushIncSearchList('https://kidp.gifu-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://sso.sugiyama-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Sugiyama Jogakuen University';
        }
        if (isAllowedType('https://sso.sugiyama-u.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://sso.sugiyama-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://sso.sugiyama-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Sugiyama Jogakuen University';
            }
            pushIncSearchList('https://sso.sugiyama-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.toyota-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Toyota College';
        }
        if (isAllowedType('https://kidp.toyota-ct.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://kidp.toyota-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.toyota-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Toyota College';
            }
            pushIncSearchList('https://kidp.toyota-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shib.nagoya-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Nagoya University';
        }
        if (isAllowedType('https://shib.nagoya-u.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://shib.nagoya-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shib.nagoya-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Nagoya University';
            }
            pushIncSearchList('https://shib.nagoya-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://islwpi01.auecc.aichi-edu.ac.jp/idp/shibboleth') {
            dispDefault = 'Aichi University of Education';
        }
        if (isAllowedType('https://islwpi01.auecc.aichi-edu.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://islwpi01.auecc.aichi-edu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://islwpi01.auecc.aichi-edu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Aichi University of Education';
            }
            pushIncSearchList('https://islwpi01.auecc.aichi-edu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://ams.juen.ac.jp/idp/shibboleth') {
            dispDefault = 'Joetsu University of Education';
        }
        if (isAllowedType('https://ams.juen.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://ams.juen.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://ams.juen.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Joetsu University of Education';
            }
            pushIncSearchList('https://ams.juen.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp1.b.cii.u-fukui.ac.jp/idp/shibboleth') {
            dispDefault = 'University of Fukui';
        }
        if (isAllowedType('https://idp1.b.cii.u-fukui.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp1.b.cii.u-fukui.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp1.b.cii.u-fukui.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'University of Fukui';
            }
            pushIncSearchList('https://idp1.b.cii.u-fukui.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin.gifu-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Gifu University';
        }
        if (isAllowedType('https://gakunin.gifu-u.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://gakunin.gifu-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin.gifu-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Gifu University';
            }
            pushIncSearchList('https://gakunin.gifu-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.iamas.ac.jp/idp/shibboleth') {
            dispDefault = 'Institute of Advanced Media Arts and Sciences';
        }
        if (isAllowedType('https://idp.iamas.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp.iamas.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.iamas.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Institute of Advanced Media Arts and Sciences';
            }
            pushIncSearchList('https://idp.iamas.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin.aitech.ac.jp/idp/shibboleth') {
            dispDefault = 'Aichi Institute of Technology';
        }
        if (isAllowedType('https://gakunin.aitech.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://gakunin.aitech.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin.aitech.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Aichi Institute of Technology';
            }
            pushIncSearchList('https://gakunin.aitech.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://ipcm2.nagaokaut.ac.jp/idp/shibboleth') {
            dispDefault = 'Nagaoka University of Technology';
        }
        if (isAllowedType('https://ipcm2.nagaokaut.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://ipcm2.nagaokaut.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://ipcm2.nagaokaut.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Nagaoka University of Technology';
            }
            pushIncSearchList('https://ipcm2.nagaokaut.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shibboleth.niigata-cn.ac.jp/idp/shibboleth') {
            dispDefault = 'Niigata College of Nursing';
        }
        if (isAllowedType('https://shibboleth.niigata-cn.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://shibboleth.niigata-cn.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shibboleth.niigata-cn.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Niigata College of Nursing';
            }
            pushIncSearchList('https://shibboleth.niigata-cn.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.nifs.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute for Fusion Science';
        }
        if (isAllowedType('https://idp.nifs.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp.nifs.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.nifs.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute for Fusion Science';
            }
            pushIncSearchList('https://idp.nifs.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shib.chukyo-u.ac.jp/idp/shibboleth') {
            dispDefault = 'CHUKYO UNIVERSITY';
        }
        if (isAllowedType('https://shib.chukyo-u.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://shib.chukyo-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shib.chukyo-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'CHUKYO UNIVERSITY';
            }
            pushIncSearchList('https://shib.chukyo-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.cais.niigata-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Niigata University';
        }
        if (isAllowedType('https://idp.cais.niigata-u.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp.cais.niigata-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.cais.niigata-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Niigata University';
            }
            pushIncSearchList('https://idp.cais.niigata-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.fujita-hu.ac.jp/idp/shibboleth') {
            dispDefault = 'Fujita Health University';
        }
        if (isAllowedType('https://idp.fujita-hu.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp.fujita-hu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.fujita-hu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Fujita Health University';
            }
            pushIncSearchList('https://idp.fujita-hu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://ku-sso.cis.kanazawa-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kanazawa University';
        }
        if (isAllowedType('https://ku-sso.cis.kanazawa-u.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://ku-sso.cis.kanazawa-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://ku-sso.cis.kanazawa-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kanazawa University';
            }
            pushIncSearchList('https://ku-sso.cis.kanazawa-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.gifu.shotoku.ac.jp/idp/shibboleth') {
            dispDefault = 'Gifu Shotoku Gakuen University';
        }
        if (isAllowedType('https://idp.gifu.shotoku.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp.gifu.shotoku.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.gifu.shotoku.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Gifu Shotoku Gakuen University';
            }
            pushIncSearchList('https://idp.gifu.shotoku.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp02.u-toyama.ac.jp/idp/shibboleth') {
            dispDefault = 'University of Toyama';
        }
        if (isAllowedType('https://idp02.u-toyama.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp02.u-toyama.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp02.u-toyama.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'University of Toyama';
            }
            pushIncSearchList('https://idp02.u-toyama.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin.ims.ac.jp/idp/shibboleth') {
            dispDefault = 'Institute for Molecular Science';
        }
        if (isAllowedType('https://gakunin.ims.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://gakunin.ims.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin.ims.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Institute for Molecular Science';
            }
            pushIncSearchList('https://gakunin.ims.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.tsuru.ac.jp/idp/shibboleth') {
            dispDefault = 'Tsuru University';
        }
        if (isAllowedType('https://idp.tsuru.ac.jp/idp/shibboleth', 'chubu') && isAllowedIdP('https://idp.tsuru.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.tsuru.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tsuru University';
            }
            pushIncSearchList('https://idp.tsuru.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://authidp1.iimc.kyoto-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kyoto University';
        }
        if (isAllowedType('https://authidp1.iimc.kyoto-u.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://authidp1.iimc.kyoto-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://authidp1.iimc.kyoto-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kyoto University';
            }
            pushIncSearchList('https://authidp1.iimc.kyoto-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin.kyoto-su.ac.jp/idp') {
            dispDefault = 'Kyoto Sangyo University';
        }
        if (isAllowedType('https://gakunin.kyoto-su.ac.jp/idp', 'kinki') && isAllowedIdP('https://gakunin.kyoto-su.ac.jp/idp')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin.kyoto-su.ac.jp/idp"
            ) {
                dispDefault = 'Kyoto Sangyo University';
            }
            pushIncSearchList('https://gakunin.kyoto-su.ac.jp/idp');
        }
        if (last_idp == 'https://fed.center.kobe-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kobe University';
        }
        if (isAllowedType('https://fed.center.kobe-u.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://fed.center.kobe-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://fed.center.kobe-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kobe University';
            }
            pushIncSearchList('https://fed.center.kobe-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.naist.jp/idp/shibboleth') {
            dispDefault = 'Nara Institute of Science and Technology';
        }
        if (isAllowedType('https://idp.naist.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.naist.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.naist.jp/idp/shibboleth"
            ) {
                dispDefault = 'Nara Institute of Science and Technology';
            }
            pushIncSearchList('https://idp.naist.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shib-idp.nara-edu.ac.jp/idp/shibboleth') {
            dispDefault = 'Nara University of Education';
        }
        if (isAllowedType('https://shib-idp.nara-edu.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://shib-idp.nara-edu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shib-idp.nara-edu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Nara University of Education';
            }
            pushIncSearchList('https://shib-idp.nara-edu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.ritsumei.ac.jp/idp/shibboleth') {
            dispDefault = 'Ritsumeikan University';
        }
        if (isAllowedType('https://idp.ritsumei.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.ritsumei.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.ritsumei.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Ritsumeikan University';
            }
            pushIncSearchList('https://idp.ritsumei.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp1.itc.kansai-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kansai University';
        }
        if (isAllowedType('https://idp1.itc.kansai-u.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp1.itc.kansai-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp1.itc.kansai-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kansai University';
            }
            pushIncSearchList('https://idp1.itc.kansai-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shib.osaka-kyoiku.ac.jp/idp/shibboleth') {
            dispDefault = 'Osaka Kyoiku University';
        }
        if (isAllowedType('https://shib.osaka-kyoiku.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://shib.osaka-kyoiku.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shib.osaka-kyoiku.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Osaka Kyoiku University';
            }
            pushIncSearchList('https://shib.osaka-kyoiku.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp1.kyokyo-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kyoto University of Education';
        }
        if (isAllowedType('https://idp1.kyokyo-u.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp1.kyokyo-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp1.kyokyo-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kyoto University of Education';
            }
            pushIncSearchList('https://idp1.kyokyo-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://authsv.kpu.ac.jp/idp/shibboleth') {
            dispDefault = 'Kyoto Prefectural University';
        }
        if (isAllowedType('https://authsv.kpu.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://authsv.kpu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://authsv.kpu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kyoto Prefectural University';
            }
            pushIncSearchList('https://authsv.kpu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.tezukayama-u.ac.jp/idp/shibboleth') {
            dispDefault = 'TEZUKAYAMA UNIVERSITY';
        }
        if (isAllowedType('https://idp.tezukayama-u.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.tezukayama-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.tezukayama-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'TEZUKAYAMA UNIVERSITY';
            }
            pushIncSearchList('https://idp.tezukayama-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.tieskun.net/idp/shibboleth') {
            dispDefault = 'CCC-TIES';
        }
        if (isAllowedType('https://idp.tieskun.net/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.tieskun.net/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.tieskun.net/idp/shibboleth"
            ) {
                dispDefault = 'CCC-TIES';
            }
            pushIncSearchList('https://idp.tieskun.net/idp/shibboleth');
        }
        if (last_idp == 'https://idp.ouhs.ac.jp/idp/shibboleth') {
            dispDefault = 'Osaka University of Health and Sport Sciences';
        }
        if (isAllowedType('https://idp.ouhs.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.ouhs.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.ouhs.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Osaka University of Health and Sport Sciences';
            }
            pushIncSearchList('https://idp.ouhs.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.maizuru-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Maizuru College';
        }
        if (isAllowedType('https://kidp.maizuru-ct.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://kidp.maizuru-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.maizuru-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Maizuru College';
            }
            pushIncSearchList('https://kidp.maizuru-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.wakayama-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Wakayama College';
        }
        if (isAllowedType('https://kidp.wakayama-nct.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://kidp.wakayama-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.wakayama-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Wakayama College';
            }
            pushIncSearchList('https://kidp.wakayama-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.akashi.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Akashi College';
        }
        if (isAllowedType('https://kidp.akashi.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://kidp.akashi.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.akashi.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Akashi College';
            }
            pushIncSearchList('https://kidp.akashi.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://g-shib.auth.oit.ac.jp/idp/shibboleth') {
            dispDefault = 'Osaka Institute of Technology';
        }
        if (isAllowedType('https://g-shib.auth.oit.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://g-shib.auth.oit.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://g-shib.auth.oit.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Osaka Institute of Technology';
            }
            pushIncSearchList('https://g-shib.auth.oit.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.nara-k.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Nara College';
        }
        if (isAllowedType('https://kidp.nara-k.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://kidp.nara-k.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.nara-k.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Nara College';
            }
            pushIncSearchList('https://kidp.nara-k.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.kobe-cufs.ac.jp/idp/shibboleth') {
            dispDefault = 'Kobe City University of Foreign Studies';
        }
        if (isAllowedType('https://idp.kobe-cufs.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.kobe-cufs.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.kobe-cufs.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kobe City University of Foreign Studies';
            }
            pushIncSearchList('https://idp.kobe-cufs.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://sumsidp.shiga-med.ac.jp/idp/shibboleth') {
            dispDefault = 'Shiga University of Medical Science';
        }
        if (isAllowedType('https://sumsidp.shiga-med.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://sumsidp.shiga-med.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://sumsidp.shiga-med.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Shiga University of Medical Science';
            }
            pushIncSearchList('https://sumsidp.shiga-med.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.kobe-tokiwa.ac.jp/idp/shibboleth') {
            dispDefault = 'Kobe Tokiwa University';
        }
        if (isAllowedType('https://idp.kobe-tokiwa.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.kobe-tokiwa.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.kobe-tokiwa.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kobe Tokiwa University';
            }
            pushIncSearchList('https://idp.kobe-tokiwa.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gakunin.osaka-cu.ac.jp/idp/shibboleth') {
            dispDefault = 'Osaka City University';
        }
        if (isAllowedType('https://gakunin.osaka-cu.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://gakunin.osaka-cu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gakunin.osaka-cu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Osaka City University';
            }
            pushIncSearchList('https://gakunin.osaka-cu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.doshisha.ac.jp/idp/shibboleth') {
            dispDefault = 'Doshisha University';
        }
        if (isAllowedType('https://idp.doshisha.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.doshisha.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.doshisha.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Doshisha University';
            }
            pushIncSearchList('https://idp.doshisha.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.kpu-m.ac.jp/idp/shibboleth') {
            dispDefault = 'Kyoto Prefectural University of Medicine';
        }
        if (isAllowedType('https://idp.kpu-m.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.kpu-m.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.kpu-m.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kyoto Prefectural University of Medicine';
            }
            pushIncSearchList('https://idp.kpu-m.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.otani.ac.jp/idp/shibboleth') {
            dispDefault = 'Otani University';
        }
        if (isAllowedType('https://idp.otani.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.otani.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.otani.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Otani University';
            }
            pushIncSearchList('https://idp.otani.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gidp.ryukoku.ac.jp/idp/shibboleth') {
            dispDefault = 'Ryukoku University';
        }
        if (isAllowedType('https://gidp.ryukoku.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://gidp.ryukoku.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gidp.ryukoku.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Ryukoku University';
            }
            pushIncSearchList('https://gidp.ryukoku.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://naraidp.cc.nara-wu.ac.jp/idp/shibboleth') {
            dispDefault = 'Nara Women\'s University';
        }
        if (isAllowedType('https://naraidp.cc.nara-wu.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://naraidp.cc.nara-wu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://naraidp.cc.nara-wu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Nara Women\'s University';
            }
            pushIncSearchList('https://naraidp.cc.nara-wu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gk-idp.auth.osaka-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Osaka University';
        }
        if (isAllowedType('https://gk-idp.auth.osaka-u.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://gk-idp.auth.osaka-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gk-idp.auth.osaka-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Osaka University';
            }
            pushIncSearchList('https://gk-idp.auth.osaka-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://heimdall.osaka-aoyama.ac.jp/idp/shibboleth') {
            dispDefault = 'Osaka Aoyama University';
        }
        if (isAllowedType('https://heimdall.osaka-aoyama.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://heimdall.osaka-aoyama.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://heimdall.osaka-aoyama.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Osaka Aoyama University';
            }
            pushIncSearchList('https://heimdall.osaka-aoyama.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.kindai.ac.jp/idp/shibboleth') {
            dispDefault = 'Kindai University';
        }
        if (isAllowedType('https://idp.kindai.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.kindai.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.kindai.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kindai University';
            }
            pushIncSearchList('https://idp.kindai.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.cis.kit.ac.jp/idp/shibboleth') {
            dispDefault = 'Kyoto Institute of Technology';
        }
        if (isAllowedType('https://idp.cis.kit.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.cis.kit.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.cis.kit.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kyoto Institute of Technology';
            }
            pushIncSearchList('https://idp.cis.kit.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.andrew.ac.jp/idp/shibboleth') {
            dispDefault = 'Momoyama Gakuin University';
        }
        if (isAllowedType('https://idp.andrew.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.andrew.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.andrew.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Momoyama Gakuin University';
            }
            pushIncSearchList('https://idp.andrew.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.kobe-ccn.ac.jp/idp/shibboleth') {
            dispDefault = 'Kobe City College of Nursing';
        }
        if (isAllowedType('https://idp.kobe-ccn.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.kobe-ccn.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.kobe-ccn.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kobe City College of Nursing';
            }
            pushIncSearchList('https://idp.kobe-ccn.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.u-hyogo.ac.jp/idp/shibboleth') {
            dispDefault = 'University of Hyogo';
        }
        if (isAllowedType('https://idp.u-hyogo.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.u-hyogo.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.u-hyogo.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'University of Hyogo';
            }
            pushIncSearchList('https://idp.u-hyogo.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.wakayama-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Wakayama University';
        }
        if (isAllowedType('https://idp.wakayama-u.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.wakayama-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.wakayama-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Wakayama University';
            }
            pushIncSearchList('https://idp.wakayama-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.21c.osakafu-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Osaka Prefecture University';
        }
        if (isAllowedType('https://idp.21c.osakafu-u.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.21c.osakafu-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.21c.osakafu-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Osaka Prefecture University';
            }
            pushIncSearchList('https://idp.21c.osakafu-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://dc-shibsv.shiga-u.ac.jp/idp/shibboleth/') {
            dispDefault = 'SHIGA UNIVERSITY';
        }
        if (isAllowedType('https://dc-shibsv.shiga-u.ac.jp/idp/shibboleth/', 'kinki') && isAllowedIdP('https://dc-shibsv.shiga-u.ac.jp/idp/shibboleth/')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://dc-shibsv.shiga-u.ac.jp/idp/shibboleth/"
            ) {
                dispDefault = 'SHIGA UNIVERSITY';
            }
            pushIncSearchList('https://dc-shibsv.shiga-u.ac.jp/idp/shibboleth/');
        }
        if (last_idp == 'https://gkn.kbu.ac.jp/idp/shibboleth') {
            dispDefault = 'Kyoto Bunkyo University';
        }
        if (isAllowedType('https://gkn.kbu.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://gkn.kbu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gkn.kbu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kyoto Bunkyo University';
            }
            pushIncSearchList('https://gkn.kbu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.osaka-ue.ac.jp/idp/shibboleth') {
            dispDefault = 'Osaka University of Economics';
        }
        if (isAllowedType('https://idp.osaka-ue.ac.jp/idp/shibboleth', 'kinki') && isAllowedIdP('https://idp.osaka-ue.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.osaka-ue.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Osaka University of Economics';
            }
            pushIncSearchList('https://idp.osaka-ue.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.hiroshima-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Hiroshima University';
        }
        if (isAllowedType('https://idp.hiroshima-u.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://idp.hiroshima-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.hiroshima-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Hiroshima University';
            }
            pushIncSearchList('https://idp.hiroshima-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://odidp.cc.okayama-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Okayama University';
        }
        if (isAllowedType('https://odidp.cc.okayama-u.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://odidp.cc.okayama-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://odidp.cc.okayama-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Okayama University';
            }
            pushIncSearchList('https://odidp.cc.okayama-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://fed.ipc.hiroshima-cu.ac.jp/idp/shibboleth') {
            dispDefault = 'Hiroshima City University';
        }
        if (isAllowedType('https://fed.ipc.hiroshima-cu.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://fed.ipc.hiroshima-cu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://fed.ipc.hiroshima-cu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Hiroshima City University';
            }
            pushIncSearchList('https://fed.ipc.hiroshima-cu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.it-hiroshima.ac.jp/idp/shibboleth') {
            dispDefault = 'Hiroshima Institute of Technology';
        }
        if (isAllowedType('https://idp.it-hiroshima.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://idp.it-hiroshima.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.it-hiroshima.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Hiroshima Institute of Technology';
            }
            pushIncSearchList('https://idp.it-hiroshima.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.shudo-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Hiroshima Shudo University';
        }
        if (isAllowedType('https://idp.shudo-u.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://idp.shudo-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.shudo-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Hiroshima Shudo University';
            }
            pushIncSearchList('https://idp.shudo-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.oshima-k.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Oshima College';
        }
        if (isAllowedType('https://kidp.oshima-k.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://kidp.oshima-k.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.oshima-k.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Oshima College';
            }
            pushIncSearchList('https://kidp.oshima-k.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.kure-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Kure College';
        }
        if (isAllowedType('https://kidp.kure-nct.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://kidp.kure-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.kure-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Kure College';
            }
            pushIncSearchList('https://kidp.kure-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.hiroshima-cmt.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Hiroshima College';
        }
        if (isAllowedType('https://kidp.hiroshima-cmt.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://kidp.hiroshima-cmt.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.hiroshima-cmt.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Hiroshima College';
            }
            pushIncSearchList('https://kidp.hiroshima-cmt.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.yonago-k.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Yonago College';
        }
        if (isAllowedType('https://kidp.yonago-k.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://kidp.yonago-k.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.yonago-k.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Yonago College';
            }
            pushIncSearchList('https://kidp.yonago-k.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.tsuyama-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Tsuyama College';
        }
        if (isAllowedType('https://kidp.tsuyama-ct.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://kidp.tsuyama-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.tsuyama-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Tsuyama College';
            }
            pushIncSearchList('https://kidp.tsuyama-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.ube-k.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Ube College';
        }
        if (isAllowedType('https://kidp.ube-k.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://kidp.ube-k.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.ube-k.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Ube College';
            }
            pushIncSearchList('https://kidp.ube-k.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.tokuyama.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Tokuyama College';
        }
        if (isAllowedType('https://kidp.tokuyama.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://kidp.tokuyama.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.tokuyama.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Tokuyama College';
            }
            pushIncSearchList('https://kidp.tokuyama.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.matsue-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Matsue College';
        }
        if (isAllowedType('https://idp.matsue-ct.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://idp.matsue-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.matsue-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Matsue College';
            }
            pushIncSearchList('https://idp.matsue-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.tottori-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Tottori University';
        }
        if (isAllowedType('https://idp.tottori-u.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://idp.tottori-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.tottori-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tottori University';
            }
            pushIncSearchList('https://idp.tottori-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.shimane-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Shimane University';
        }
        if (isAllowedType('https://idp.shimane-u.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://idp.shimane-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.shimane-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Shimane University';
            }
            pushIncSearchList('https://idp.shimane-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.oka-pu.ac.jp/idp/shibboleth') {
            dispDefault = 'Okayama Prefectural University';
        }
        if (isAllowedType('https://idp.oka-pu.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://idp.oka-pu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.oka-pu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Okayama Prefectural University';
            }
            pushIncSearchList('https://idp.oka-pu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.pu-hiroshima.ac.jp/idp/shibboleth') {
            dispDefault = 'Prefectural University of Hiroshima';
        }
        if (isAllowedType('https://idp.pu-hiroshima.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://idp.pu-hiroshima.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.pu-hiroshima.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Prefectural University of Hiroshima';
            }
            pushIncSearchList('https://idp.pu-hiroshima.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://auth.socu.ac.jp/idp/shibboleth') {
            dispDefault = 'Sanyo-Onoda City University';
        }
        if (isAllowedType('https://auth.socu.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://auth.socu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://auth.socu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Sanyo-Onoda City University';
            }
            pushIncSearchList('https://auth.socu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.cc.yamaguchi-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Yamaguchi University';
        }
        if (isAllowedType('https://idp.cc.yamaguchi-u.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://idp.cc.yamaguchi-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.cc.yamaguchi-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Yamaguchi University';
            }
            pushIncSearchList('https://idp.cc.yamaguchi-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.pub.ous.ac.jp/idp/shibboleth') {
            dispDefault = 'Okayama University of Science';
        }
        if (isAllowedType('https://idp.pub.ous.ac.jp/idp/shibboleth', 'chugoku') && isAllowedIdP('https://idp.pub.ous.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.pub.ous.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Okayama University of Science';
            }
            pushIncSearchList('https://idp.pub.ous.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.cc.ehime-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Ehime University';
        }
        if (isAllowedType('https://idp.cc.ehime-u.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://idp.cc.ehime-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.cc.ehime-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Ehime University';
            }
            pushIncSearchList('https://idp.cc.ehime-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://gidp.ait230.tokushima-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Tokushima University';
        }
        if (isAllowedType('https://gidp.ait230.tokushima-u.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://gidp.ait230.tokushima-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://gidp.ait230.tokushima-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Tokushima University';
            }
            pushIncSearchList('https://gidp.ait230.tokushima-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.kochi-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Kochi College';
        }
        if (isAllowedType('https://kidp.kochi-ct.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://kidp.kochi-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.kochi-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Kochi College';
            }
            pushIncSearchList('https://kidp.kochi-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://ktidp.kagawa-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Kagawa College';
        }
        if (isAllowedType('https://ktidp.kagawa-nct.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://ktidp.kagawa-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://ktidp.kagawa-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Kagawa College';
            }
            pushIncSearchList('https://ktidp.kagawa-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.yuge.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Yuge College';
        }
        if (isAllowedType('https://kidp.yuge.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://kidp.yuge.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.yuge.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Yuge College';
            }
            pushIncSearchList('https://kidp.yuge.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.niihama-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Niihama College';
        }
        if (isAllowedType('https://kidp.niihama-nct.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://kidp.niihama-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.niihama-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Niihama College';
            }
            pushIncSearchList('https://kidp.niihama-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.anan-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Anan College';
        }
        if (isAllowedType('https://kidp.anan-nct.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://kidp.anan-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.anan-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Anan College';
            }
            pushIncSearchList('https://kidp.anan-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.kochi-tech.ac.jp/idp/shibboleth') {
            dispDefault = 'Kochi University of Technology';
        }
        if (isAllowedType('https://idp.kochi-tech.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://idp.kochi-tech.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.kochi-tech.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kochi University of Technology';
            }
            pushIncSearchList('https://idp.kochi-tech.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://aries.naruto-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Naruto University of Education';
        }
        if (isAllowedType('https://aries.naruto-u.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://aries.naruto-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://aries.naruto-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Naruto University of Education';
            }
            pushIncSearchList('https://aries.naruto-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp1.matsuyama-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Matsuyama University';
        }
        if (isAllowedType('https://idp1.matsuyama-u.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://idp1.matsuyama-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp1.matsuyama-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Matsuyama University';
            }
            pushIncSearchList('https://idp1.matsuyama-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.kochi-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kochi University';
        }
        if (isAllowedType('https://idp.kochi-u.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://idp.kochi-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.kochi-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kochi University';
            }
            pushIncSearchList('https://idp.kochi-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.itc.kagawa-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kagawa University';
        }
        if (isAllowedType('https://idp.itc.kagawa-u.ac.jp/idp/shibboleth', 'shikoku') && isAllowedIdP('https://idp.itc.kagawa-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.itc.kagawa-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kagawa University';
            }
            pushIncSearchList('https://idp.itc.kagawa-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://ssoidp.cc.saga-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Saga University';
        }
        if (isAllowedType('https://ssoidp.cc.saga-u.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://ssoidp.cc.saga-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://ssoidp.cc.saga-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Saga University';
            }
            pushIncSearchList('https://ssoidp.cc.saga-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.isc.kyutech.ac.jp/idp/shibboleth') {
            dispDefault = 'Kyushu Institute of Technology';
        }
        if (isAllowedType('https://idp.isc.kyutech.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://idp.isc.kyutech.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.isc.kyutech.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kyushu Institute of Technology';
            }
            pushIncSearchList('https://idp.isc.kyutech.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.kyushu-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kyushu University';
        }
        if (isAllowedType('https://idp.kyushu-u.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://idp.kyushu-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.kyushu-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kyushu University';
            }
            pushIncSearchList('https://idp.kyushu-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://um-idp.cc.miyazaki-u.ac.jp/idp/shibboleth') {
            dispDefault = 'University of Miyazaki';
        }
        if (isAllowedType('https://um-idp.cc.miyazaki-u.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://um-idp.cc.miyazaki-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://um-idp.cc.miyazaki-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'University of Miyazaki';
            }
            pushIncSearchList('https://um-idp.cc.miyazaki-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://fed.u-ryukyu.ac.jp/shibboleth') {
            dispDefault = 'University of the Ryukyus';
        }
        if (isAllowedType('https://fed.u-ryukyu.ac.jp/shibboleth', 'kyushu') && isAllowedIdP('https://fed.u-ryukyu.ac.jp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://fed.u-ryukyu.ac.jp/shibboleth"
            ) {
                dispDefault = 'University of the Ryukyus';
            }
            pushIncSearchList('https://fed.u-ryukyu.ac.jp/shibboleth');
        }
        if (last_idp == 'https://kidp.kct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Kitakyushu College';
        }
        if (isAllowedType('https://kidp.kct.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://kidp.kct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.kct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Kitakyushu College';
            }
            pushIncSearchList('https://kidp.kct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shibboleth-idp.bene.fit.ac.jp/idp/shibboleth') {
            dispDefault = 'Fukuoka Institute of Technology';
        }
        if (isAllowedType('https://shibboleth-idp.bene.fit.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://shibboleth-idp.bene.fit.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shibboleth-idp.bene.fit.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Fukuoka Institute of Technology';
            }
            pushIncSearchList('https://shibboleth-idp.bene.fit.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shib.kumamoto-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kumamoto University';
        }
        if (isAllowedType('https://shib.kumamoto-u.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://shib.kumamoto-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shib.kumamoto-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kumamoto University';
            }
            pushIncSearchList('https://shib.kumamoto-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.oita-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Oita College';
        }
        if (isAllowedType('https://kidp.oita-ct.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://kidp.oita-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.oita-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Oita College';
            }
            pushIncSearchList('https://kidp.oita-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.sasebo.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Sasebo College';
        }
        if (isAllowedType('https://kidp.sasebo.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://kidp.sasebo.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.sasebo.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Sasebo College';
            }
            pushIncSearchList('https://kidp.sasebo.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.kagoshima-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Kagoshima College';
        }
        if (isAllowedType('https://kidp.kagoshima-ct.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://kidp.kagoshima-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.kagoshima-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Kagoshima College';
            }
            pushIncSearchList('https://kidp.kagoshima-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.kurume-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Kurume College';
        }
        if (isAllowedType('https://kidp.kurume-nct.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://kidp.kurume-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.kurume-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Kurume College';
            }
            pushIncSearchList('https://kidp.kurume-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.miyakonojo-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Miyakonojo College';
        }
        if (isAllowedType('https://kidp.miyakonojo-nct.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://kidp.miyakonojo-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.miyakonojo-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Miyakonojo College';
            }
            pushIncSearchList('https://kidp.miyakonojo-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.ariake-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Ariake College';
        }
        if (isAllowedType('https://kidp.ariake-nct.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://kidp.ariake-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.ariake-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Ariake College';
            }
            pushIncSearchList('https://kidp.ariake-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.kumamoto-nct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Kumamoto College';
        }
        if (isAllowedType('https://kidp.kumamoto-nct.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://kidp.kumamoto-nct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.kumamoto-nct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Kumamoto College';
            }
            pushIncSearchList('https://kidp.kumamoto-nct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.okinawa-ct.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Technology,Okinawa College';
        }
        if (isAllowedType('https://kidp.okinawa-ct.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://kidp.okinawa-ct.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.okinawa-ct.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Technology,Okinawa College';
            }
            pushIncSearchList('https://kidp.okinawa-ct.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://shibboleth-idp.kyusan-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kyushu Sangyo University';
        }
        if (isAllowedType('https://shibboleth-idp.kyusan-u.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://shibboleth-idp.kyusan-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://shibboleth-idp.kyusan-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kyushu Sangyo University';
            }
            pushIncSearchList('https://shibboleth-idp.kyusan-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://logon.oist.jp/idp/shibboleth') {
            dispDefault = 'Okinawa Institute of Science and Technology Graduate University';
        }
        if (isAllowedType('https://logon.oist.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://logon.oist.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://logon.oist.jp/idp/shibboleth"
            ) {
                dispDefault = 'Okinawa Institute of Science and Technology Graduate University';
            }
            pushIncSearchList('https://logon.oist.jp/idp/shibboleth');
        }
        if (last_idp == 'https://nuidp.nagasaki-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Nagasaki University';
        }
        if (isAllowedType('https://nuidp.nagasaki-u.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://nuidp.nagasaki-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://nuidp.nagasaki-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Nagasaki University';
            }
            pushIncSearchList('https://nuidp.nagasaki-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.seinan-gu.ac.jp/idp/shibboleth') {
            dispDefault = 'Seinan Gakuin University';
        }
        if (isAllowedType('https://idp.seinan-gu.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://idp.seinan-gu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.seinan-gu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Seinan Gakuin University';
            }
            pushIncSearchList('https://idp.seinan-gu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.net.oita-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Oita University';
        }
        if (isAllowedType('https://idp.net.oita-u.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://idp.net.oita-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.net.oita-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Oita University';
            }
            pushIncSearchList('https://idp.net.oita-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://kidp.cc.kagoshima-u.ac.jp/idp/shibboleth') {
            dispDefault = 'Kagoshima University';
        }
        if (isAllowedType('https://kidp.cc.kagoshima-u.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://kidp.cc.kagoshima-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://kidp.cc.kagoshima-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kagoshima University';
            }
            pushIncSearchList('https://kidp.cc.kagoshima-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.nifs-k.ac.jp/idp/shibboleth') {
            dispDefault = 'National Institute of Fitness and Sports in KANOYA';
        }
        if (isAllowedType('https://idp.nifs-k.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://idp.nifs-k.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.nifs-k.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'National Institute of Fitness and Sports in KANOYA';
            }
            pushIncSearchList('https://idp.nifs-k.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://ss.fukuoka-edu.ac.jp/idp/shibboleth') {
            dispDefault = 'University of Teacher Education Fukuoka';
        }
        if (isAllowedType('https://ss.fukuoka-edu.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://ss.fukuoka-edu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://ss.fukuoka-edu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'University of Teacher Education Fukuoka';
            }
            pushIncSearchList('https://ss.fukuoka-edu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.sun.ac.jp/idp/shibboleth') {
            dispDefault = 'University of Nagasaki';
        }
        if (isAllowedType('https://idp.sun.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://idp.sun.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.sun.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'University of Nagasaki';
            }
            pushIncSearchList('https://idp.sun.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.okiu.ac.jp/idp/shibboleth') {
            dispDefault = 'Okinawa International University';
        }
        if (isAllowedType('https://idp.okiu.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://idp.okiu.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.okiu.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Okinawa International University';
            }
            pushIncSearchList('https://idp.okiu.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.sojo-u.ac.jp/idp/shibboleth') {
            dispDefault = 'SOJO University';
        }
        if (isAllowedType('https://idp.sojo-u.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://idp.sojo-u.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.sojo-u.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'SOJO University';
            }
            pushIncSearchList('https://idp.sojo-u.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.kurume-it.ac.jp/idp/shibboleth') {
            dispDefault = 'Kurume Institute of Technology';
        }
        if (isAllowedType('https://idp.kurume-it.ac.jp/idp/shibboleth', 'kyushu') && isAllowedIdP('https://idp.kurume-it.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.kurume-it.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'Kurume Institute of Technology';
            }
            pushIncSearchList('https://idp.kurume-it.ac.jp/idp/shibboleth');
        }
        if (last_idp == 'https://idp.gakunin.nii.ac.jp/idp/shibboleth') {
            dispDefault = 'GakuNin IdP';
        }
        if (isAllowedType('https://idp.gakunin.nii.ac.jp/idp/shibboleth', 'others') && isAllowedIdP('https://idp.gakunin.nii.ac.jp/idp/shibboleth')) {
            if (
                "-" == "-" &&
                typeof(wayf_default_idp) != "undefined" &&
                wayf_default_idp == "https://idp.gakunin.nii.ac.jp/idp/shibboleth"
            ) {
                dispDefault = 'GakuNin IdP';
            }
            pushIncSearchList('https://idp.gakunin.nii.ac.jp/idp/shibboleth');
        }
        if (wayf_additional_idps.length > 0) {
            var listcnt = inc_search_list.length;

            // Show additional IdPs in the order they are defined
            for (var i = 0; i < wayf_additional_idps.length; i++) {
                if (wayf_additional_idps[i]) {
                    // Last used IdP is known because of local _saml_idp cookie
                    if (
                        wayf_additional_idps[i].name &&
                        wayf_additional_idps[i].entityID == last_idp
                    ) {
                        dispDefault = wayf_additional_idps[i].name;
                        inc_search_list[listcnt] = new Array();
                        inc_search_list[listcnt][0] = wayf_additional_idps[i].entityID;
                        inc_search_list[listcnt][1] = "From other federations";
                        inc_search_list[listcnt][2] = wayf_additional_idps[i].name;
                        inc_search_list[listcnt][3] = wayf_additional_idps[i].name;
                        listcnt++;
                    }
                    // If no IdP is known but the default IdP matches, use this entry
                    else if (
                        wayf_additional_idps[i].name &&
                        typeof(wayf_default_idp) != "undefined" &&
                        wayf_additional_idps[i].entityID == wayf_default_idp
                    ) {
                        dispDefault = wayf_additional_idps[i].name;
                        inc_search_list[listcnt] = new Array();
                        inc_search_list[listcnt][0] = wayf_additional_idps[i].entityID;
                        inc_search_list[listcnt][1] = "From other federations";
                        inc_search_list[listcnt][2] = wayf_additional_idps[i].name;
                        inc_search_list[listcnt][3] = wayf_additional_idps[i].name;
                        listcnt++;
                    } else if (wayf_additional_idps[i].name) {
                        inc_search_list[listcnt] = new Array();
                        inc_search_list[listcnt][0] = wayf_additional_idps[i].entityID;
                        inc_search_list[listcnt][1] = "From other federations";
                        inc_search_list[listcnt][2] = wayf_additional_idps[i].name;
                        inc_search_list[listcnt][3] = wayf_additional_idps[i].name;
                        listcnt++;
                    }
                }
            }

        }
        writeHTML('<div style="clear:both;"></div>');
        writeHTML('<table border="0" cellpadding="0" cellspacing="0" style="width: 100%;">');
        writeHTML('<tr>');
        writeHTML('<td id="keytext_td" style="width: 100%;">');
        if (dispDefault == '') {
            dispidp = initdisp;
        } else {
            dispidp = dispDefault;
        }
        writeHTML('<input id="keytext" type="text" name="pattern" value="" autocomplete="off" size="60" tabindex=5 style="float: left; width: 100%; display: block"/>');

        writeHTML('<div style="clear:both;"></div>');
        writeHTML('<div id="view_incsearch_base">');
        writeHTML('<div id="view_incsearch_animate" style="height:' + wayf_list_height + ';">');
        writeHTML('<div id="view_incsearch_scroll" style="height:' + wayf_list_height + ';">');
        writeHTML('<div id="view_incsearch"></div>');
        writeHTML('</div>');
        writeHTML('</div>');
        writeHTML('</div>');
        writeHTML('</td>');

        writeHTML('<td>');
        writeHTML('<img id="dropdown_img" src="https://ds.gakunin.nii.ac.jp/GakuNinDS/images/dropdown_down.png" title="Display/non-display of IdP list" tabindex=6 style="border:0px; width:20px; height:20px; vertical-align:middle;">');
        writeHTML('</td>');

        writeHTML('<td>');
        writeHTML('&nbsp;');
        writeHTML('</td>');

        writeHTML('<td>');
        // Do we have to display custom text?
        if (typeof(wayf_overwrite_submit_button_text) == "undefined") {
            writeHTML('<input id="wayf_submit_button" type="submit" name="Login" accesskey="s" value="Login" tabindex="10" ');
        } else {
            writeHTML('<input id="wayf_submit_button" type="submit" name="Login" accesskey="s" value="' + wayf_overwrite_submit_button_text + '" tabindex="10" ');
        }

        if (dispidp == initdisp) {
            writeHTML('disabled >');
        } else {
            writeHTML('>');
        }

        writeHTML('</td>');
        writeHTML('</tr>');


        writeHTML('<tr>');
        writeHTML('<td colspan="3">');
        // Draw checkbox
        writeHTML('<div id="wayf_remember_checkbox_div" style="float: left;margin-top: 0px;margin-bottom:0px; width: 100%;">');
        // Do we have to show the remember settings checkbox?
        if (wayf_show_remember_checkbox) {
            // Is the checkbox forced to be checked
            if (wayf_force_remember_for_session) {
                // First draw the dummy checkbox ...
                writeHTML('<input id="wayf_remember_checkbox" type="checkbox" name="session_dummy" value="true" tabindex=8 checked="checked" disabled="disabled" >&nbsp;');
                // ... and now the real but hidden checkbox
                writeHTML('<input type="hidden" name="session" value="true">&nbsp;');
            } else {
                writeHTML('<input id="wayf_remember_checkbox" type="checkbox" name="session" value="true" tabindex=8 >&nbsp;');
            }

            // Do we have to display custom text?
            if (typeof(wayf_overwrite_checkbox_label_text) == "undefined") {
                writeHTML('<label for="wayf_remember_checkbox" id="wayf_remember_checkbox_label" style="min-width:80px; font-size:' + wayf_font_size + 'px;color:' + wayf_font_color + ';">Remember selection for this web browser session.</label>');

            } else if (wayf_overwrite_checkbox_label_text != "") {
                writeHTML('<label for="wayf_remember_checkbox" id="wayf_remember_checkbox_label" style="min-width:80px; font-size:' + wayf_font_size + 'px;color:' + wayf_font_color + ';">' + wayf_overwrite_checkbox_label_text + '</label>');
            }
        } else if (wayf_force_remember_for_session) {
            // Is the checkbox forced to be checked but hidden
            writeHTML('<input id="wayf_remember_checkbox" type="hidden" name="session" value="true">&nbsp;');
        }
        writeHTML('</div>');
        writeHTML('</td>');

        writeHTML('<td style="vertical-align:middle; text-align:center;">');
        writeHTML('<div id="clear_a" class="default" title="A search key is emptied and it is the list display of all the IdP(s)." tabindex=11>Reset</div>');
        writeHTML('</td>');
        writeHTML('</tr>');
        writeHTML('</table>');

        // Close form
        writeHTML('</form>');

    } // End login check

    // Close box
    writeHTML('</div>');
    writeHTML('<div style="clear:both;"></div>');

    // Now output HTML all at once
    document.write(wayf_html);
})()
