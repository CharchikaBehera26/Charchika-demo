import re

from .data_store import read_data
from .faq import cached_faqs


LANGUAGES = ("en", "or", "hi")

EN = {
    "signin": "Use the artisan and SHG portal to sign in and manage your public profile or product listings.",
    "register": "Create an artisan or SHG account to publish a profile and manage marketplace listings. You can add an exact public map location from your profile later.",
    "map": "The map is centered on Odisha. It shows exact public pins only for makers who have added coordinates to their profile.",
    "find": "Browse maker profiles by name, craft or district. You can also use the map to see profiles that have shared an exact public location.",
    "sell_in": "You are signed in. Add a product listing from your maker workspace.",
    "sell_out": "To sell through the demonstration marketplace, first create a maker account. Already registered? Sign in to manage your listings.",
    "buy": "The marketplace contains demonstration listings. Open a product listing to discover its maker and craft.",
    "scheme": "The scheme finder contains illustrative information only. Confirm eligibility, availability and application details with the official department before applying.",
    "story": "Explore short introductions to Odisha's living craft traditions and the people who carry them forward.",
    "community": "You can share an encouraging note with the SrujanSetu community.",
    "hello": "Namaskar! I can answer questions using the site's craft information and guide you to artisans, the map, marketplace, stories, community or scheme finder. What would you like to do?",
    "crafts": "The craft directory covers Odisha traditions, including Pattachitra, Sambalpuri Ikat, Pipili Appliqué, Silver Filigree, Terracotta and Dhokra.",
    "fallback": "I couldn't find that in the site's information yet. I can help with Odisha crafts, finding artisans, exact map locations, marketplace listings, community posts and scheme information.",
}

HI = {
    "signin": "कारीगर और स्वयं सहायता समूह पोर्टल में साइन इन करके अपनी सार्वजनिक प्रोफ़ाइल और उत्पाद सूची संभालें।",
    "register": "प्रोफ़ाइल और बाज़ार सूची के लिए कारीगर या स्वयं सहायता समूह खाता बनाएँ। बाद में प्रोफ़ाइल से सार्वजनिक नक्शे का स्थान भी जोड़ सकते हैं।",
    "map": "नक्शा ओडिशा पर केंद्रित है। पिन तभी दिखता है जब कारीगर ने अपनी प्रोफ़ाइल में निर्देशांक जोड़े हों।",
    "find": "नाम, शिल्प या ज़िले से कारीगर खोजें। जिन्होंने सार्वजनिक स्थान साझा किया है, वे नक्शे पर भी दिखते हैं।",
    "sell_in": "आप साइन इन हैं। अपने कार्यक्षेत्र से उत्पाद सूची जोड़ें।",
    "sell_out": "प्रदर्शन बाज़ार में बेचने के लिए पहले कारीगर खाता बनाएँ। खाता है तो साइन इन करके सूची संभालें।",
    "buy": "बाज़ार में प्रदर्शन सूचियाँ हैं। उत्पाद खोलकर उसके कारीगर और शिल्प को जानें।",
    "scheme": "योजना कार्ड केवल उदाहरण हैं। आवेदन से पहले आधिकारिक विभाग से पात्रता और विवरण जाँच लें।",
    "story": "ओडिशा की जीवित शिल्प परंपराओं और उन्हें आगे बढ़ाने वाले लोगों की छोटी कहानियाँ पढ़ें।",
    "community": "आप श्रीजनसेतु समुदाय के लिए एक संदेश छोड़ सकते हैं।",
    "hello": "नमस्कार! मैं शिल्प, कारीगर, नक्शा, बाज़ार, कहानियाँ, समुदाय और योजनाओं में मदद कर सकता हूँ। आप क्या करना चाहते हैं?",
    "crafts": "शिल्प सूची में पट्टचित्र, संबलपुरी इकत, पिपिली अप्लिक, चाँदी की तारकसी, टेराकोटा और ढोकरा शामिल हैं।",
    "fallback": "यह बात अभी साइट की जानकारी में नहीं मिली। मैं ओडिशा के शिल्प, कारीगर, नक्शा, बाज़ार, समुदाय और योजनाओं में मदद कर सकता हूँ।",
}

OR = {
    "signin": "କାରିଗର ଓ ସ୍ୱୟଂ ସହାୟକ ଗୋଷ୍ଠୀ ପୋର୍ଟାଲରେ ସାଇନ୍ ଇନ୍ କରି ଆପଣଙ୍କ ସାର୍ବଜନୀନ ପ୍ରୋଫାଇଲ୍ ଓ ଉତ୍ପାଦ ତାଲିକା ପରିଚାଳନା କରନ୍ତୁ।",
    "register": "ପ୍ରୋଫାଇଲ୍ ଓ ବଜାର ତାଲିକା ପାଇଁ କାରିଗର କିମ୍ବା ସ୍ୱୟଂ ସହାୟକ ଗୋଷ୍ଠୀ ଖାତା ତିଆରି କରନ୍ତୁ। ପରେ ପ୍ରୋଫାଇଲରୁ ସାର୍ବଜନୀନ ମାନଚିତ୍ର ସ୍ଥାନ ଯୋଡ଼ିପାରିବେ।",
    "map": "ମାନଚିତ୍ର ଓଡ଼ିଶା ଉପରେ କେନ୍ଦ୍ରିତ। କାରିଗର ନିଜ ପ୍ରୋଫାଇଲରେ ସ୍ଥାନାଙ୍କ ଦେଲେ ହିଁ ପିନ୍ ଦେଖାଯାଏ।",
    "find": "ନାମ, ଶିଳ୍ପ କିମ୍ବା ଜିଲ୍ଲା ଅନୁସାରେ କାରିଗର ଖୋଜନ୍ତୁ। ଯେଉଁମାନେ ସାର୍ବଜନୀନ ସ୍ଥାନ ଦେଇଛନ୍ତି ସେମାନେ ମାନଚିତ୍ରରେ ମଧ୍ୟ ଦେଖାଯିବେ।",
    "sell_in": "ଆପଣ ସାଇନ୍ ଇନ୍ ଅଛନ୍ତି। ନିଜ କାର୍ଯ୍ୟକ୍ଷେତ୍ରରୁ ଉତ୍ପାଦ ତାଲିକା ଯୋଡ଼ନ୍ତୁ।",
    "sell_out": "ପ୍ରଦର୍ଶନ ବଜାରରେ ବିକ୍ରୟ ପାଇଁ ପ୍ରଥମେ କାରିଗର ଖାତା ତିଆରି କରନ୍ତୁ। ଖାତା ଥିଲେ ସାଇନ୍ ଇନ୍ କରି ତାଲିକା ପରିଚାଳନା କରନ୍ତୁ।",
    "buy": "ବଜାରରେ ପ୍ରଦର୍ଶନ ତାଲିକା ଅଛି। ଉତ୍ପାଦ ଖୋଲି ତା’ର କାରିଗର ଓ ଶିଳ୍ପ ଜାଣନ୍ତୁ।",
    "scheme": "ଯୋଜନା କାର୍ଡ କେବଳ ଉଦାହରଣ। ଆବେଦନ ଆଗରୁ ସରକାରୀ ବିଭାଗରୁ ଯୋଗ୍ୟତା ଓ ବିବରଣୀ ଯାଞ୍ଚ କରନ୍ତୁ।",
    "story": "ଓଡ଼ିଶାର ଜୀବନ୍ତ ଶିଳ୍ପ ପରମ୍ପରା ଓ ତାକୁ ଆଗକୁ ନେଉଥିବା ଲୋକଙ୍କ ଛୋଟ କାହାଣୀ ପଢ଼ନ୍ତୁ।",
    "community": "ଆପଣ ଶ୍ରୁଜନସେତୁ ସମୁଦାୟ ପାଇଁ ଏକ ସନ୍ଦେଶ ରଖିପାରିବେ।",
    "hello": "ନମସ୍କାର! ମୁଁ ଶିଳ୍ପ, କାରିଗର, ମାନଚିତ୍ର, ବଜାର, କାହାଣୀ, ସମୁଦାୟ ଓ ଯୋଜନାରେ ସାହାଯ୍ୟ କରିପାରିବି। ଆପଣ କ’ଣ କରିବାକୁ ଚାହୁଁଛନ୍ତି?",
    "crafts": "ଶିଳ୍ପ ତାଲିକାରେ ପଟ୍ଟଚିତ୍ର, ସମ୍ବଲପୁରୀ ଇକତ, ପିପିଲି ଆପ୍ଲିକ, ରୂପା ତାରକସି, ଟେରାକୋଟା ଓ ଢୋକରା ଅଛି।",
    "fallback": "ଏହା ଏଯାଏଁ ସାଇଟ୍ ତଥ୍ୟରେ ମିଳିଲା ନାହିଁ। ମୁଁ ଓଡ଼ିଶାର ଶିଳ୍ପ, କାରିଗର, ମାନଚିତ୍ର, ବଜାର, ସମୁଦାୟ ଓ ଯୋଜନାରେ ସାହାଯ୍ୟ କରିପାରିବି।",
}

REPLIES = {"en": EN, "hi": HI, "or": OR}

CRAFT_TEXT = {
    "Pattachitra": {
        "hi": "पट्टचित्र कपड़े पर बारीक रेखाओं और प्राकृतिक रंगों से पौराणिक कथाएँ चित्रित करने की परंपरा है। यह रघुराजपुर, पुरी से जुड़ी है।",
        "or": "ପଟ୍ଟଚିତ୍ର ହେଉଛି କପଡ଼ା ଉପରେ ସୂକ୍ଷ୍ମ ରେଖା ଓ ପ୍ରାକୃତିକ ରଙ୍ଗରେ ପୌରାଣିକ କାହାଣୀ ଅଙ୍କନ। ଏହା ରଘୁରାଜପୁର, ପୁରୀ ସହ ଜଡ଼ିତ।",
    },
    "Sambalpuri Ikat": {
        "hi": "संबलपुरी इकत में धागों को बुनने से पहले बाँधकर रंगा जाता है। यह संबलपुर और बड़गढ़ की हथकरघा परंपरा है।",
        "or": "ସମ୍ବଲପୁରୀ ଇକତରେ ବୁଣା ଆଗରୁ ସୂତାକୁ ବାନ୍ଧି ରଙ୍ଗ କରାଯାଏ। ଏହା ସମ୍ବଲପୁର ଓ ବରଗଡ଼ର ହସ୍ତତନ୍ତ ପରମ୍ପରା।",
    },
    "Pipili Appliqué": {
        "hi": "पिपिली अप्लिक में रंगीन कपड़े के टुकड़े सिलकर छाता, चँदोवा और सजावट बनती है। यह पुरी के पिपिली से जुड़ी है।",
        "or": "ପିପିଲି ଆପ୍ଲିକରେ ରଙ୍ଗୀନ କପଡ଼ା ଟୁକୁଡ଼ା ସିଲେଇ କରି ଛତା, ଚାନ୍ଦୁଆ ଓ ସଜାବଟ ତିଆରି ହୁଏ। ଏହା ପୁରୀର ପିପିଲି ସହ ଜଡ଼ିତ।",
    },
    "Silver Filigree": {
        "hi": "कटक की चाँदी की तारकसी में बारीक चाँदी के तारों से गहने और सजावटी वस्तुएँ बनती हैं।",
        "or": "କଟକର ତାରକସିରେ ସୂକ୍ଷ୍ମ ରୂପା ତାରରୁ ଗହଣା ଓ ସାଜସଜ୍ଜା ତିଆରି ହୁଏ।",
    },
    "Terracotta": {
        "hi": "ओडिशा की टेराकोटा में मिट्टी को हाथ से गढ़कर आँच में पकाया जाता है। यह रोज़मर्रा की ज़िंदगी, पूजा और लोक कल्पना को आकार देती है।",
        "or": "ଓଡ଼ିଶାର ଟେରାକୋଟାରେ ମାଟିକୁ ହାତରେ ଗଢ଼ି ନିଆଁରେ ପୋଡ଼ାଯାଏ। ଏହା ଦୈନନ୍ଦିନ ଜୀବନ, ପୂଜା ଓ ଲୋକ କଳ୍ପନାକୁ ଆକାର ଦିଏ।",
    },
    "Dhokra Metal Craft": {
        "hi": "ढोकरा धातु शिल्प में खोई हुई मोम की ढलाई से मूर्तियाँ और वस्तुएँ बनती हैं। यह ढेंकानाल और मयूरभंज से जुड़ा है।",
        "or": "ଢୋକରା ଧାତୁ ଶିଳ୍ପରେ ହଜିଯାଇଥିବା ମହମ ଢାଳି ଦ୍ୱାରା ମୂର୍ତ୍ତି ଓ ବସ୍ତୁ ତିଆରି ହୁଏ। ଏହା ଢେଙ୍କାନାଳ ଓ ମୟୂରଭଞ୍ଜ ସହ ଜଡ଼ିତ।",
    },
}

FAQ_TEXT = {
    "Hi / hello": {
        "hi": "नमस्कार! मैं श्रीजनसेतु गाइड हूँ। ओडिशा के शिल्प के बारे में पूछें, या बताएँ कि आप कारीगर, नक्शा, खरीदारी या कारीगर के रूप में जुड़ना चाहते हैं।",
        "or": "ନମସ୍କାର! ମୁଁ ଶ୍ରୁଜନସେତୁ ଗାଇଡ୍। ଓଡ଼ିଶାର ଶିଳ୍ପ ବିଷୟରେ ପଚାରନ୍ତୁ, କିମ୍ବା କୁହନ୍ତୁ ଯେ ଆପଣ କାରିଗର, ମାନଚିତ୍ର, କିଣିବା କିମ୍ବା କାରିଗର ଭାବେ ଯୋଗ ଦେବାକୁ ଚାହୁଁଛନ୍ତି।",
    },
    "What is SrujanSetu?": {
        "hi": "श्रीजनसेतु एक शैक्षिक परियोजना है जो ओडिशा के शिल्प, कारीगर और स्वयं सहायता समूह प्रोफ़ाइल, एक नमूना बाज़ार और नक्शा एक जगह दिखाती है।",
        "or": "ଶ୍ରୁଜନସେତୁ ଏକ ଶିକ୍ଷାମୂଳକ ପ୍ରକଳ୍ପ। ଏହା ଓଡ଼ିଶାର ଶିଳ୍ପ, କାରିଗର ଓ ସ୍ୱୟଂ ସହାୟକ ଗୋଷ୍ଠୀ ପ୍ରୋଫାଇଲ୍, ଏକ ନମୁନା ବଜାର ଓ ମାନଚିତ୍ରକୁ ଏକାଠି ରଖେ।",
    },
    "What can I ask the guide?": {
        "hi": "मैं इस साइट और ओडिशा के शिल्प आँकड़ों पर आम सवालों के जवाब देकर आपको कारीगर, नक्शा, बाज़ार, कहानियाँ, समुदाय या योजनाओं तक ले जा सकता हूँ।",
        "or": "ମୁଁ ଏହି ସାଇଟ୍ ଓ ଓଡ଼ିଶା ଶିଳ୍ପ ତଥ୍ୟ ଉପରେ ସାଧାରଣ ପ୍ରଶ୍ନର ଉତ୍ତର ଦେଇ ଆପଣଙ୍କୁ କାରିଗର, ମାନଚିତ୍ର, ବଜାର, କାହାଣୀ, ସମୁଦାୟ କିମ୍ବା ଯୋଜନା ପର୍ଯ୍ୟନ୍ତ ନେଇପାରିବି।",
    },
    "What is an SHG?": {
        "hi": "SHG का अर्थ स्वयं सहायता समूह है। यह साइट कारीगरों और समूहों को अपना काम दिखाने और ग्राहकों तक पहुँचने में मदद के लिए बनी है।",
        "or": "SHG ଅର୍ଥ ସ୍ୱୟଂ ସହାୟକ ଗୋଷ୍ଠୀ। ଏହି ସାଇଟ୍ କାରିଗର ଓ ଗୋଷ୍ଠୀମାନଙ୍କୁ ସେମାନଙ୍କ କାମ ଦେଖାଇବା ଓ ଗ୍ରାହକଙ୍କ ପାଖରେ ପହଞ୍ଚିବାରେ ସାହାଯ୍ୟ ପାଇଁ ତିଆରି।",
    },
    "How do I find artisans near me?": {
        "hi": "शिल्प या ज़िले से प्रोफ़ाइल देखें, या ओडिशा का नक्शा खोलें। सटीक पिन तभी दिखता है जब कारीगर ने सार्वजनिक कार्यशाला या दुकान के निर्देशांक जोड़े हों।",
        "or": "ଶିଳ୍ପ କିମ୍ବା ଜିଲ୍ଲା ଅନୁସାରେ ପ୍ରୋଫାଇଲ୍ ଦେଖନ୍ତୁ, କିମ୍ବା ଓଡ଼ିଶା ମାନଚିତ୍ର ଖୋଲନ୍ତୁ। କାରିଗର ସାର୍ବଜନୀନ କର୍ମଶାଳା କିମ୍ବା ଦୋକାନର ସ୍ଥାନାଙ୍କ ଦେଲେ ହିଁ ସଠିକ୍ ପିନ୍ ଦେଖାଯାଏ।",
    },
    "Why are there no pins on the map?": {
        "hi": "नक्शा कारीगर का स्थान अनुमान नहीं लगाता। प्रोफ़ाइल पर पिन तभी आता है जब मालिक अक्षांश और देशांतर दोनों जोड़ दे।",
        "or": "ମାନଚିତ୍ର କାରିଗରଙ୍କ ସ୍ଥାନ ଅନୁମାନ କରେ ନାହିଁ। ମାଲିକ ଅକ୍ଷାଂଶ ଓ ଦ୍ରାଘିମା ଉଭୟ ଯୋଡ଼ିଲେ ହିଁ ପ୍ରୋଫାଇଲ୍ ପିନ୍ ହୁଏ।",
    },
    "How do I register as an artisan or SHG?": {
        "hi": "नाम, ईमेल, शिल्प या उत्पाद श्रेणी और ज़िले के साथ कारीगर खाता बनाएँ। पंजीकरण के बाद प्रोफ़ाइल बदलें और सार्वजनिक स्थान तभी जोड़ें जब आप उसे नक्शे पर दिखाना चाहें।",
        "or": "ନାମ, ଇମେଲ୍, ଶିଳ୍ପ କିମ୍ବା ଉତ୍ପାଦ ଶ୍ରେଣୀ ଓ ଜିଲ୍ଲା ସହ କାରିଗର ଖାତା ତିଆରି କରନ୍ତୁ। ପଞ୍ଜିକରଣ ପରେ ପ୍ରୋଫାଇଲ୍ ବଦଳାନ୍ତୁ ଓ ମାନଚିତ୍ରରେ ଦେଖାଇବାକୁ ଚାହିଁଲେ ହିଁ ସାର୍ବଜନୀନ ସ୍ଥାନ ଯୋଡ଼ନ୍ତୁ।",
    },
    "How do I add or update my products?": {
        "hi": "कारीगर खाते में साइन इन करें, डैशबोर्ड खोलें और My Products चुनें। वहाँ सूची जोड़, बदल या हटा सकते हैं।",
        "or": "କାରିଗର ଖାତାରେ ସାଇନ୍ ଇନ୍ କରନ୍ତୁ, ଡ୍ୟାସବୋର୍ଡ ଖୋଲନ୍ତୁ ଓ My Products ବାଛନ୍ତୁ। ସେଠାରେ ତାଲିକା ଯୋଡ଼ି, ବଦଳାଇ କିମ୍ବା ହଟାଇପାରିବେ।",
    },
    "How do I add a product photo?": {
        "hi": "साइन इन करके My Products खोलें, सूची जोड़ें या बदलें, और 5 एमबी से छोटी PNG, JPG, GIF या WEBP तस्वीर चुनें।",
        "or": "ସାଇନ୍ ଇନ୍ କରି My Products ଖୋଲନ୍ତୁ, ତାଲିକା ଯୋଡ଼ନ୍ତୁ କିମ୍ବା ବଦଳାନ୍ତୁ, ଓ 5 MBରୁ ଛୋଟ PNG, JPG, GIF କିମ୍ବା WEBP ଛବି ବାଛନ୍ତୁ।",
    },
    "Can I buy products on this site?": {
        "hi": "बाज़ार अभी केवल प्रदर्शन सूचियाँ दिखाता है। यह ऑर्डर या भुगतान नहीं लेता। असली शुरुआत से पहले संपर्क और चेकआउट जोड़ना होगा।",
        "or": "ବଜାର ବର୍ତ୍ତମାନ କେବଳ ପ୍ରଦର୍ଶନ ତାଲିକା ଦେଖାଏ। ଏହା ଅର୍ଡର କିମ୍ବା ପେମେଣ୍ଟ ନେଏ ନାହିଁ। ପ୍ରକୃତ ଆରମ୍ଭ ଆଗରୁ ଯୋଗାଯୋଗ ଓ ଚେକଆଉଟ୍ ଯୋଡ଼ିବାକୁ ପଡ଼ିବ।",
    },
    "How can I contact a maker?": {
        "hi": "इस डेमो में सीधा संदेश और सत्यापित संपर्क अभी उपलब्ध नहीं है। उत्पाद सूचियाँ नमूना हैं, जीवित ऑफ़र नहीं।",
        "or": "ଏହି ଡେମୋରେ ସିଧା ବାର୍ତ୍ତା ଓ ଯାଞ୍ଚିତ ଯୋଗାଯୋଗ ଏଯାଏଁ ନାହିଁ। ଉତ୍ପାଦ ତାଲିକା ନମୁନା, ସଚଳ ଅଫର ନୁହେଁ।",
    },
    "Do I have to pay to register?": {
        "hi": "इस प्रदर्शन पंजीकरण में भुगतान नहीं माँगा जाता। असली शुरुआत से पहले कारीगरों के लिए सत्यापित शर्तें और गोपनीयता जानकारी प्रकाशित करें।",
        "or": "ଏହି ପ୍ରଦର୍ଶନ ପଞ୍ଜିକରଣରେ ଦେୟ ମାଗାଯାଏ ନାହିଁ। ପ୍ରକୃତ ଆରମ୍ଭ ଆଗରୁ କାରିଗରଙ୍କ ପାଇଁ ଯାଞ୍ଚିତ ସର୍ତ୍ତ ଓ ଗୋପନୀୟତା ତଥ୍ୟ ପ୍ରକାଶ କରନ୍ତୁ।",
    },
    "Are the government schemes verified?": {
        "hi": "नहीं। योजना कार्ड उदाहरण हैं, सत्यापित या चालू सरकारी मार्गदर्शन नहीं। वर्तमान पात्रता आधिकारिक विभाग से जाँचें।",
        "or": "ନା। ଯୋଜନା କାର୍ଡ ଉଦାହରଣ, ଯାଞ୍ଚିତ କିମ୍ବା ସଚଳ ସରକାରୀ ମାର୍ଗଦର୍ଶନ ନୁହେଁ। ବର୍ତ୍ତମାନ ଯୋଗ୍ୟତା ସରକାରୀ ବିଭାଗରୁ ଯାଞ୍ଚ କରନ୍ତୁ।",
    },
    "How can I change my profile or map location?": {
        "hi": "कारीगर पोर्टल में साइन इन करें और Edit profile खोलें। सार्वजनिक पिन के लिए अक्षांश और देशांतर दोनों भरें, या दोनों खाली छोड़कर पिन हटाएँ। केवल वही पता साझा करें जिसे आप सार्वजनिक करना चाहते हैं।",
        "or": "କାରିଗର ପୋର୍ଟାଲରେ ସାଇନ୍ ଇନ୍ କରି Edit profile ଖୋଲନ୍ତୁ। ସାର୍ବଜନୀନ ପିନ୍ ପାଇଁ ଅକ୍ଷାଂଶ ଓ ଦ୍ରାଘିମା ଉଭୟ ଦିଅନ୍ତୁ, କିମ୍ବା ଉଭୟ ଖାଲି ରଖି ପିନ୍ ହଟାନ୍ତୁ। ଯେଉଁ ଠିକଣା ସାର୍ବଜନୀନ କରିବାକୁ ସହଜ ଲାଗେ କେବଳ ତାହା ଦିଅନ୍ତୁ।",
    },
    "Can I reset my password?": {
        "hi": "इस डेमो में स्वयं पासवर्ड पुनर्प्राप्ति उपलब्ध नहीं है। साइट व्यवस्थापक से संपर्क करें। चैट में पासवर्ड न लिखें।",
        "or": "ଏହି ଡେମୋରେ ନିଜେ ପାସୱାର୍ଡ ପୁନରୁଦ୍ଧାର ନାହିଁ। ସାଇଟ୍ ପ୍ରଶାସକଙ୍କୁ ଯୋଗାଯୋଗ କରନ୍ତୁ। ଚାଟ୍‌ରେ ପାସୱାର୍ଡ ଲେଖନ୍ତୁ ନାହିଁ।",
    },
    "Are the assistant answers generated by AI?": {
        "hi": "गाइड, बिक्री सहायक और कथा लेखक इस साइट के रिकॉर्ड से अंग्रेज़ी, ओड़िया और हिंदी में जवाब देते हैं। वे आपका सवाल किसी बाहरी एआई सेवा को नहीं भेजते।",
        "or": "ଗାଇଡ୍, ବିକ୍ରୟ ସହାୟକ ଓ କାହାଣୀ ଲେଖକ ଏହି ସାଇଟ୍ ରେକର୍ଡରୁ ଇଂରାଜୀ, ଓଡ଼ିଆ ଓ ହିନ୍ଦୀରେ ଉତ୍ତର ଦିଅନ୍ତି। ସେମାନେ ଆପଣଙ୍କ ପ୍ରଶ୍ନକୁ ବାହ୍ୟ AI ସେବାକୁ ପଠାନ୍ତି ନାହିଁ।",
    },
    "Where is Odisha?": {
        "hi": "ओडिशा भारत के पूर्वी तट पर, बंगाल की खाड़ी के साथ एक राज्य है। यह साइट उसके शिल्प समुदायों और कारीगर प्रोफ़ाइल पर केंद्रित है।",
        "or": "ଓଡ଼ିଶା ଭାରତର ପୂର୍ବ ଉପକୂଳରେ, ବଙ୍ଗୋପସାଗର କୂଳରେ ଥିବା ଏକ ରାଜ୍ୟ। ଏହି ସାଇଟ୍ ତା’ର ଶିଳ୍ପ ସମୁଦାୟ ଓ କାରିଗର ପ୍ରୋଫାଇଲ୍ ଉପରେ କେନ୍ଦ୍ରିତ।",
    },
    "Thank you": {
        "hi": "आपका स्वागत है! शिल्प देखने, कारीगर खोजने या साइट पर चलने में मैं मदद के लिए हूँ।",
        "or": "ସ୍ୱାଗତ! ଶିଳ୍ପ ଦେଖିବା, କାରିଗର ଖୋଜିବା କିମ୍ବା ସାଇଟ୍ ବୁଲିବାରେ ମୁଁ ସାହାଯ୍ୟ ପାଇଁ ଅଛି।",
    },
    "Goodbye": {
        "hi": "श्रीजनसेतु आने के लिए धन्यवाद। ओडिशा के कारीगरों और शिल्प को देखने कभी भी लौटें।",
        "or": "ଶ୍ରୁଜନସେତୁକୁ ଆସିଥିବାରୁ ଧନ୍ୟବାଦ। ଓଡ଼ିଶାର କାରିଗର ଓ ଶିଳ୍ପ ଦେଖିବାକୁ ଯେକୌଣସି ସମୟରେ ଫେରନ୍ତୁ।",
    },
}

LABELS = {
    "Open artisan sign in": {"hi": "कारीगर साइन इन खोलें", "or": "କାରିଗର ସାଇନ୍ ଇନ୍ ଖୋଲନ୍ତୁ"},
    "Create a maker account": {"hi": "कारीगर खाता बनाएँ", "or": "କାରିଗର ଖାତା ତିଆରି କରନ୍ତୁ"},
    "Sign in": {"hi": "साइन इन", "or": "ସାଇନ୍ ଇନ୍"},
    "Open the artisan map": {"hi": "कारीगर नक्शा खोलें", "or": "କାରିଗର ମାନଚିତ୍ର ଖୋଲନ୍ତୁ"},
    "Browse all artisan profiles": {"hi": "सभी प्रोफ़ाइल देखें", "or": "ସବୁ ପ୍ରୋଫାଇଲ୍ ଦେଖନ୍ତୁ"},
    "Find artisans": {"hi": "कारीगर खोजें", "or": "କାରିଗର ଖୋଜନ୍ତୁ"},
    "Add a product": {"hi": "उत्पाद जोड़ें", "or": "ଉତ୍ପାଦ ଯୋଡ଼ନ୍ତୁ"},
    "Explore the SHG marketplace": {"hi": "बाज़ार देखें", "or": "ବଜାର ଦେଖନ୍ତୁ"},
    "Ask the sell assistant": {"hi": "बिक्री सहायक से पूछें", "or": "ବିକ୍ରୟ ସହାୟକଙ୍କୁ ପଚାରନ୍ତୁ"},
    "Open the scheme finder": {"hi": "योजना खोजें", "or": "ଯୋଜନା ଖୋଜନ୍ତୁ"},
    "Read craft stories": {"hi": "शिल्प कथाएँ पढ़ें", "or": "ଶିଳ୍ପ କାହାଣୀ ପଢ଼ନ୍ତୁ"},
    "Write a craft story": {"hi": "शिल्प कथा लिखें", "or": "ଶିଳ୍ପ କାହାଣୀ ଲେଖନ୍ତୁ"},
    "Visit the community": {"hi": "समुदाय खोलें", "or": "ସମୁଦାୟ ଖୋଲନ୍ତୁ"},
    "Explore this craft": {"hi": "यह शिल्प देखें", "or": "ଏହି ଶିଳ୍ପ ଦେଖନ୍ତୁ"},
    "Find its makers": {"hi": "इसके कारीगर खोजें", "or": "ଏହାର କାରିଗର ଖୋଜନ୍ତୁ"},
    "Explore crafts": {"hi": "शिल्प देखें", "or": "ଶିଳ୍ପ ଦେଖନ୍ତୁ"},
    "Visit the marketplace": {"hi": "बाज़ार खोलें", "or": "ବଜାର ଖୋଲନ୍ତୁ"},
    "Browse schemes": {"hi": "योजनाएँ देखें", "or": "ଯୋଜନା ଦେଖନ୍ତୁ"},
    "Browse Odisha crafts": {"hi": "ओडिशा के शिल्प देखें", "or": "ଓଡ଼ିଶା ଶିଳ୍ପ ଦେଖନ୍ତୁ"},
    "Open the map": {"hi": "नक्शा खोलें", "or": "ମାନଚିତ୍ର ଖୋଲନ୍ତୁ"},
    "Ask another question": {"hi": "एक और सवाल पूछें", "or": "ଆଉ ଏକ ପ୍ରଶ୍ନ ପଚାରନ୍ତୁ"},
    "About SrujanSetu": {"hi": "श्रीजनसेतु के बारे में", "or": "ଶ୍ରୁଜନସେତୁ ବିଷୟରେ"},
    "Join as a maker": {"hi": "कारीगर बनकर जुड़ें", "or": "କାରିଗର ଭାବେ ଯୋଗ ଦିଅନ୍ତୁ"},
    "Browse artisans": {"hi": "कारीगर देखें", "or": "କାରିଗର ଦେଖନ୍ତୁ"},
    "Maker sign in": {"hi": "कारीगर साइन इन", "or": "କାରିଗର ସାଇନ୍ ଇନ୍"},
    "Open the marketplace": {"hi": "बाज़ार खोलें", "or": "ବଜାର ଖୋଲନ୍ତୁ"},
    "Browse sample products": {"hi": "नमूना उत्पाद देखें", "or": "ନମୁନା ଉତ୍ପାଦ ଦେଖନ୍ତୁ"},
    "Browse artisan profiles": {"hi": "कारीगर प्रोफ़ाइल देखें", "or": "କାରିଗର ପ୍ରୋଫାଇଲ୍ ଦେଖନ୍ତୁ"},
    "Open scheme information": {"hi": "योजना जानकारी खोलें", "or": "ଯୋଜନା ତଥ୍ୟ ଖୋଲନ୍ତୁ"},
    "Open the maker portal": {"hi": "कारीगर पोर्टल खोलें", "or": "କାରିଗର ପୋର୍ଟାଲ ଖୋଲନ୍ତୁ"},
    "Browse the FAQ": {"hi": "प्रश्न देखें", "or": "ପ୍ରଶ୍ନ ଦେଖନ୍ତୁ"},
    "Explore the Odisha map": {"hi": "ओडिशा का नक्शा देखें", "or": "ଓଡ଼ିଶା ମାନଚିତ୍ର ଦେଖନ୍ତୁ"},
    "Return home": {"hi": "होम पर जाएँ", "or": "ହୋମକୁ ଯାଆନ୍ତୁ"},
}

CHROME = {
    "en": {
        "home": "Home",
        "crafts": "Explore Crafts",
        "artisans": "Find Artisans",
        "map": "Explore Map",
        "market": "SHG Marketplace",
        "stories": "Craft Stories",
        "schemes": "Schemes & Support",
        "about": "About Us",
        "guide": "Guide",
        "sell": "Sell",
        "story": "Stories",
        "back": "Back",
        "artisan_portal": "Artisan Portal",
        "admin": "Admin",
        "help_b": "Need Help?",
        "help_s": "Chat with the Guide",
        "footer_help": "Need help finding something? Ask SrujanSetu Guide →",
        "agents": "Agents",
        "footer_blurb": "Discover Odisha’s living crafts, meet the makers and support artisan and SHG communities.",
    },
    "hi": {
        "home": "होम",
        "crafts": "शिल्प देखें",
        "artisans": "कारीगर खोजें",
        "map": "नक्शा",
        "market": "बाज़ार",
        "stories": "शिल्प कथाएँ",
        "schemes": "योजनाएँ",
        "about": "हमारे बारे में",
        "guide": "गाइड",
        "sell": "बिक्री सहायक",
        "story": "कथा",
        "back": "वापस",
        "artisan_portal": "कारीगर पोर्टल",
        "admin": "एडमिन",
        "help_b": "मदद चाहिए?",
        "help_s": "गाइड से बात करें",
        "footer_help": "कुछ खोजना है? श्रीजनसेतु गाइड से पूछें →",
        "agents": "सहायक",
        "footer_blurb": "ओडिशा के जीवित शिल्प खोजें, कारीगरों से मिलें और स्वयं सहायता समूहों का साथ दें।",
    },
    "or": {
        "home": "ହୋମ",
        "crafts": "ଶିଳ୍ପ ଦେଖନ୍ତୁ",
        "artisans": "କାରିଗର ଖୋଜନ୍ତୁ",
        "map": "ମାନଚିତ୍ର",
        "market": "ବଜାର",
        "stories": "ଶିଳ୍ପ କାହାଣୀ",
        "schemes": "ଯୋଜନା",
        "about": "ଆମ ବିଷୟରେ",
        "guide": "ଗାଇଡ୍",
        "sell": "ବିକ୍ରୟ ସହାୟକ",
        "story": "କାହାଣୀ",
        "back": "ପଛକୁ",
        "artisan_portal": "କାରିଗର ପୋର୍ଟାଲ",
        "admin": "ଆଡମିନ",
        "help_b": "ସାହାଯ୍ୟ ଚାହିଁବେ?",
        "help_s": "ଗାଇଡ୍ ସହ କଥା ହୁଅନ୍ତୁ",
        "footer_help": "କିଛି ଖୋଜୁଛନ୍ତି? ଶ୍ରୁଜନସେତୁ ଗାଇଡ୍‌କୁ ପଚାରନ୍ତୁ →",
        "agents": "ସହାୟକ",
        "footer_blurb": "ଓଡ଼ିଶାର ଜୀବନ୍ତ ଶିଳ୍ପ ଖୋଜନ୍ତୁ, କାରିଗରଙ୍କୁ ଭେଟନ୍ତୁ ଓ ସ୍ୱୟଂ ସହାୟକ ଗୋଷ୍ଠୀକୁ ସାହାଯ୍ୟ କରନ୍ତୁ।",
    },
}

PAGE = {
    "en": {
        "guide_kicker": "YOUR DIGITAL SAATHI",
        "guide_title_html": "Ask the <em>SrujanSetu Guide</em>",
        "guide_lead": "Ask in English, Odia or Hindi about crafts, artisans, the map or marketplace. Answers come from this site’s records.",
        "guide_name": "SrujanSetu Guide",
        "guide_status": "English · ଓଡ଼ିଆ · हिंदी",
        "guide_ready": "Ready to help",
        "guide_hello": "Namaskar! Ask me about a craft such as Pattachitra, or tell me what you would like to do.",
        "guide_placeholder": "For example: What is Pattachitra?",
        "send": "Send",
        "faq": "Frequently asked questions",
        "faq_note": "Questions are listed in English. The answer follows the language you select.",
        "guide_note": "The guide answers from the project’s craft information. It does not send your question to an external AI service. Do not enter passwords or private information.",
        "sell_kicker": "HELP A BUYER CHOOSE",
        "sell_title_html": "Ask the <em>sell assistant</em>",
        "sell_lead": "Describe a gift, a budget or a craft. The assistant recommends demonstration listings and can write a short sales caption.",
        "sell_name": "SrujanSetu Sell Assistant",
        "sell_hello": "Namaskar! Tell me who the piece is for, a craft you like, or a budget such as under 1500.",
        "sell_placeholder": "For example: A gift under 1500, or write a caption for the Sambalpuri stole",
        "sell_note": "Recommendations use the sample marketplace only. This is not a live checkout, and captions are written from the listing text.",
        "story_kicker": "KNOW THE STORY. VALUE THE SKILL.",
        "story_title_html": "Craft <em>Stories</em>",
        "story_lead": "Read the living traditions of Odisha, or weave a new short story from a craft in the catalog.",
        "story_form_title": "Weave a story",
        "story_craft": "Craft",
        "story_focus": "Focus",
        "story_language": "Language",
        "focus_making": "How it is made",
        "focus_maker": "The maker",
        "focus_gift": "A gift story",
        "story_submit": "Weave story",
        "story_note": "The story is composed from this site’s craft, maker and product records in the language you choose.",
        "empty_story": "Craft stories will be added soon.",
        "saved_stories": "Stories on the site",
    },
    "hi": {
        "guide_kicker": "आपका डिजिटल साथी",
        "guide_title_html": "<em>श्रीजनसेतु गाइड</em> से पूछें",
        "guide_lead": "शिल्प, कारीगर, नक्शा या बाज़ार के बारे में अंग्रेज़ी, ओड़िया या हिंदी में पूछें। जवाब इस साइट के रिकॉर्ड से आते हैं।",
        "guide_name": "श्रीजनसेतु गाइड",
        "guide_status": "English · ଓଡ଼ିଆ · हिंदी",
        "guide_ready": "मदद के लिए तैयार",
        "guide_hello": "नमस्कार! पट्टचित्र जैसे किसी शिल्प के बारे में पूछें, या बताएँ कि आप क्या करना चाहते हैं।",
        "guide_placeholder": "उदाहरण: पट्टचित्र क्या है?",
        "send": "भेजें",
        "faq": "अक्सर पूछे जाने वाले प्रश्न",
        "faq_note": "प्रश्न अंग्रेज़ी में सूचीबद्ध हैं। जवाब आपकी चुनी भाषा में होगा।",
        "guide_note": "गाइड परियोजना की शिल्प जानकारी से जवाब देता है। वह आपका सवाल बाहरी एआई सेवा को नहीं भेजता। पासवर्ड या निजी जानकारी न लिखें।",
        "sell_kicker": "खरीदार को चुनने में मदद",
        "sell_title_html": "<em>बिक्री सहायक</em> से पूछें",
        "sell_lead": "उपहार, बजट या शिल्प बताएँ। सहायक प्रदर्शन सूचियाँ सुझाएगा और एक छोटा बिक्री वाक्य लिख सकता है।",
        "sell_name": "श्रीजनसेतु बिक्री सहायक",
        "sell_hello": "नमस्कार! बताएँ यह किसके लिए है, कौन सा शिल्प पसंद है, या बजट जैसे 1500 से कम।",
        "sell_placeholder": "उदाहरण: 1500 से कम का उपहार, या संबलपुरी स्टोल का कैप्शन लिखें",
        "sell_note": "सुझाव केवल नमूना बाज़ार से हैं। यह जीवित चेकआउट नहीं है। कैप्शन सूची के पाठ से लिखे जाते हैं।",
        "story_kicker": "कहानी जानें। हुनर की कद्र करें।",
        "story_title_html": "शिल्प <em>कथाएँ</em>",
        "story_lead": "ओडिशा की जीवित परंपराएँ पढ़ें, या सूची के किसी शिल्प से एक नई छोटी कहानी बुनें।",
        "story_form_title": "एक कहानी बुनें",
        "story_craft": "शिल्प",
        "story_focus": "केंद्र",
        "story_language": "भाषा",
        "focus_making": "यह कैसे बनता है",
        "focus_maker": "कारीगर",
        "focus_gift": "एक उपहार कहानी",
        "story_submit": "कहानी बुनें",
        "story_note": "कहानी इस साइट के शिल्प, कारीगर और उत्पाद रिकॉर्ड से आपकी चुनी भाषा में बनती है।",
        "empty_story": "शिल्प कथाएँ जल्द जोड़ी जाएँगी।",
        "saved_stories": "साइट पर कहानियाँ",
    },
    "or": {
        "guide_kicker": "ଆପଣଙ୍କ ଡିଜିଟାଲ ସାଥୀ",
        "guide_title_html": "<em>ଶ୍ରୁଜନସେତୁ ଗାଇଡ୍</em>‌କୁ ପଚାରନ୍ତୁ",
        "guide_lead": "ଶିଳ୍ପ, କାରିଗର, ମାନଚିତ୍ର କିମ୍ବା ବଜାର ବିଷୟରେ ଇଂରାଜୀ, ଓଡ଼ିଆ କିମ୍ବା ହିନ୍ଦୀରେ ପଚାରନ୍ତୁ। ଉତ୍ତର ଏହି ସାଇଟ୍ ରେକର୍ଡରୁ ଆସେ।",
        "guide_name": "ଶ୍ରୁଜନସେତୁ ଗାଇଡ୍",
        "guide_status": "English · ଓଡ଼ିଆ · हिंदी",
        "guide_ready": "ସାହାଯ୍ୟ ପାଇଁ ପ୍ରସ୍ତୁତ",
        "guide_hello": "ନମସ୍କାର! ପଟ୍ଟଚିତ୍ର ପରି ଏକ ଶିଳ୍ପ ବିଷୟରେ ପଚାରନ୍ତୁ, କିମ୍ବା ଆପଣ କ’ଣ କରିବାକୁ ଚାହୁଁଛନ୍ତି କୁହନ୍ତୁ।",
        "guide_placeholder": "ଉଦାହରଣ: ପଟ୍ଟଚିତ୍ର କଣ?",
        "send": "ପଠାନ୍ତୁ",
        "faq": "ବାରମ୍ବାର ପଚରାଯାଉଥିବା ପ୍ରଶ୍ନ",
        "faq_note": "ପ୍ରଶ୍ନ ଇଂରାଜୀରେ ତାଲିକାଭୁକ୍ତ। ଉତ୍ତର ଆପଣ ବାଛିଥିବା ଭାଷାରେ ହେବ।",
        "guide_note": "ଗାଇଡ୍ ପ୍ରକଳ୍ପର ଶିଳ୍ପ ତଥ୍ୟରୁ ଉତ୍ତର ଦିଏ। ସେ ଆପଣଙ୍କ ପ୍ରଶ୍ନକୁ ବାହ୍ୟ AI ସେବାକୁ ପଠାଏ ନାହିଁ। ପାସୱାର୍ଡ କିମ୍ବା ବ୍ୟକ୍ତିଗତ ତଥ୍ୟ ଲେଖନ୍ତୁ ନାହିଁ।",
        "sell_kicker": "ଜଣେ କ୍ରେତାଙ୍କୁ ବାଛିବାରେ ସାହାଯ୍ୟ",
        "sell_title_html": "<em>ବିକ୍ରୟ ସହାୟକ</em>ଙ୍କୁ ପଚାରନ୍ତୁ",
        "sell_lead": "ଏକ ଉପହାର, ବଜେଟ୍ କିମ୍ବା ଶିଳ୍ପ ବର୍ଣ୍ଣନା କରନ୍ତୁ। ସହାୟକ ପ୍ରଦର୍ଶନ ତାଲିକା ସୁଝାଇବ ଓ ଏକ ଛୋଟ ବିକ୍ରୟ ବାକ୍ୟ ଲେଖିପାରିବ।",
        "sell_name": "ଶ୍ରୁଜନସେତୁ ବିକ୍ରୟ ସହାୟକ",
        "sell_hello": "ନମସ୍କାର! କୁହନ୍ତୁ ଏହା କାହା ପାଇଁ, କେଉଁ ଶିଳ୍ପ ଭଲ ଲାଗେ, କିମ୍ବା 1500ରୁ କମ୍ ପରି ଏକ ବଜେଟ୍।",
        "sell_placeholder": "ଉଦାହରଣ: 1500ରୁ କମ୍ ଉପହାର, କିମ୍ବା ସମ୍ବଲପୁରୀ ଷ୍ଟୋଲ୍ ପାଇଁ ଏକ କ୍ୟାପସନ୍ ଲେଖନ୍ତୁ",
        "sell_note": "ସୁପାରିଶ କେବଳ ନମୁନା ବଜାରରୁ। ଏହା ସଚଳ ଚେକଆଉଟ୍ ନୁହେଁ। କ୍ୟାପସନ୍ ତାଲିକା ପାଠ୍ୟରୁ ଲେଖାଯାଏ।",
        "story_kicker": "କାହାଣୀ ଜାଣନ୍ତୁ। କୌଶଳକୁ ମୂଲ୍ୟ ଦିଅନ୍ତୁ।",
        "story_title_html": "ଶିଳ୍ପ <em>କାହାଣୀ</em>",
        "story_lead": "ଓଡ଼ିଶାର ଜୀବନ୍ତ ପରମ୍ପରା ପଢ଼ନ୍ତୁ, କିମ୍ବା ତାଲିକାର ଏକ ଶିଳ୍ପରୁ ନୂଆ ଛୋଟ କାହାଣୀ ବୁଣନ୍ତୁ।",
        "story_form_title": "ଏକ କାହାଣୀ ବୁଣନ୍ତୁ",
        "story_craft": "ଶିଳ୍ପ",
        "story_focus": "କେନ୍ଦ୍ର",
        "story_language": "ଭାଷା",
        "focus_making": "ଏହା କିପରି ତିଆରି",
        "focus_maker": "କାରିଗର",
        "focus_gift": "ଏକ ଉପହାର କାହାଣୀ",
        "story_submit": "କାହାଣୀ ବୁଣନ୍ତୁ",
        "story_note": "କାହାଣୀ ଏହି ସାଇଟ୍‌ର ଶିଳ୍ପ, କାରିଗର ଓ ଉତ୍ପାଦ ରେକର୍ଡରୁ ଆପଣ ବାଛିଥିବା ଭାଷାରେ ତିଆରି ହୁଏ।",
        "empty_story": "ଶିଳ୍ପ କାହାଣୀ ଶୀଘ୍ର ଯୋଡ଼ାଯିବ।",
        "saved_stories": "ସାଇଟ୍‌ରେ ଥିବା କାହାଣୀ",
    },
}


def normalize_lang(value):
    if value in LANGUAGES:
        return value
    return "en"


def chrome_for(lang):
    return CHROME[normalize_lang(lang)]


def page_copy(lang):
    return PAGE[normalize_lang(lang)]


def language_from_message(message, fallback):
    if re.search(r"[\u0B00-\u0B7F]", message or ""):
        return "or"
    if re.search(r"[\u0900-\u097F]", message or ""):
        return "hi"
    return normalize_lang(fallback)


def localize_guide(answer, actions, lang):
    lang = normalize_lang(lang)
    if lang != "en":
        for faq in cached_faqs():
            if answer == faq.answer and faq.question in FAQ_TEXT:
                answer = FAQ_TEXT[faq.question][lang]
                break
        else:
            matched = next((key for key, text in EN.items() if text == answer), None)
            if matched:
                answer = REPLIES[lang][matched]
            else:
                for craft in read_data("crafts"):
                    name = craft.get("name", "")
                    if name and answer.startswith(f"{name}:") and name in CRAFT_TEXT:
                        answer = CRAFT_TEXT[name][lang]
                        break
    localized_actions = []
    for action in actions:
        label = action["label"]
        if lang != "en" and label in LABELS:
            label = LABELS[label][lang]
        localized_actions.append({**action, "label": label})
    return answer, localized_actions
