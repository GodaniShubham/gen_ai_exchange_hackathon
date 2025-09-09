const moods = JSON.parse(localStorage.getItem("moods")) || [];

const i18n = {
  en: {
    "hero.title": "Human support, at AI scale",
    "hero.desc": "Saharathi AI guides young minds through stress, anxiety, and uncertainty — private, 24/7 support in culturally inclusive design.",
    "hero.cta": "Get Started",
    "hero.anonymous": "No account needed – get started and explore all features anonymously.",
    "hero.b1": "Secure & private",
    "hero.b2": "Built for Gen Z",
    "hero.b3": "Available 24/7",
    "mood.title": "How are you feeling today?",
    "mood.subtitle": "Slide to pick your mood, then submit.",
    "mood.submit": "Submit",
    "mood.saved": "Saved ✅",
    "mood.analytics": "Mood Analytics",
    "mood.notePh": "Add a note (optional)",
    "mission.1.title": "Proactive support",
    "mission.1.body": "Daily check-ins detect early stress and suggest steps.",
    "mission.2.title": "Private by design",
    "mission.2.body": "Your conversations are encrypted and under your control.",
    "mission.3.title": "Inclusive guidance",
    "mission.3.body": "Culturally aware prompts help every user feel supported.",
    "how.title": "How it works",
    "how.s1.title": "Share & reflect",
    "how.s1.body": "Talk in a safe space. We listen first, then guide gently.",
    "how.s2.title": "Tailored guidance",
    "how.s2.body": "Receive exercises matching your goals — breathing, journaling, self-care.",
    "how.s3.title": "Grow with insights",
    "how.s3.body": "See progress trends and celebrate small wins.",
    "trust.title": "Trust & Safety",
    "trust.1.title": "Expert Oversight",
    "trust.1.body": "Advisors review content. Crisis escalates to human help.",
    "trust.2.title": "Data Transparency",
    "trust.2.body": "Transparent model. You control your data anytime.",
    "trust.3.title": "Accessible Design",
    "trust.3.body": "Accessibility: high contrast, screen-reader friendly.",
    "solutions.schools.title": "For schools & NGOs",
    "solutions.schools.desc": "Deploy a co-pilot for counsellors and mentors. Aggregate, anonymized insights help you support more students without burning out teams.",
    "solutions.families.title": "For families",
    "solutions.families.desc": "Build healthy routines at home with reminders, shared check-ins, and age-aware content for teens and young adults.",
    "activities.title": "Explore Guided Activities",
    "activities.subtitle": "Discover mindfulness exercises, journaling prompts, and self-care guides to support your mental wellness journey.",
    "activities.breathing.title": "Breath & Reset",
    "activities.breathing.desc": "Sync your breathing with a calming rhythm to find peace in the moment.",
    "activities.journal.title": "Journal Your Thoughts",
    "activities.journal.desc": "Reflect on guided prompts to process emotions and gain clarity.",
    "activities.selfcare.title": "Self-Care Guides",
    "activities.selfcare.desc": "Curated tips and micro-content for daily wellness and self-care routines.",
    "activities.cta": "Discover More Activities",
  },
  hi: {
    "hero.title": "मानवीय सहयोग, AI पैमाने पर",
    "hero.desc": "Saharathi AI तनाव, चिंता और अनिश्चितता में युवाओं का मार्गदर्शन करता है — निजी, 24/7 सहयोग सांस्कृतिक रूप से समावेशी डिज़ाइन के साथ।",
    "hero.cta": "शुरू करें",
    "hero.anonymous": "कोई खाता जरूरी नहीं – शुरू करें और सभी सुविधाएँ अनाम रूप से उपयोग करें।",
    "hero.b1": "सुरक्षित और निजी",
    "hero.b2": "Gen Z के लिए बनाया गया",
    "hero.b3": "24/7 उपलब्ध",
    "mood.title": "आज आप कैसा महसूस कर रहे हैं?",
    "mood.subtitle": "स्लाइडर को खींचकर अपना मूड चुनें, फिर सबमिट करें।",
    "mood.submit": "सबमिट",
    "mood.saved": "सेव ✅",
    "mood.analytics": "मूड एनालिटिक्स",
    "mood.notePh": "नोट जोड़ें (वैकल्पिक)",
    "mission.1.title": "प्रोएक्टिव सहयोग",
    "mission.1.body": "दैनिक चेक-इन शुरुआती तनाव पहचानते हैं और सुझाव देते हैं।",
    "mission.2.title": "निजी डिज़ाइन",
    "mission.2.body": "आपकी बातचीत एन्क्रिप्टेड और आपके नियंत्रण में है।",
    "mission.3.title": "समावेशी मार्गदर्शन",
    "mission.3.body": "सांस्कृतिक रूप से जागरूक प्रॉम्प्ट सभी उपयोगकर्ताओं को सहयोग देते हैं।",
    "how.title": "कैसे काम करता है",
    "how.s1.title": "अपनी बात रखें",
    "how.s1.body": "सुरक्षित स्थान पर बात करें। हम पहले सुनते हैं फिर धीरे मार्गदर्शन करते हैं।",
    "how.s2.title": "आपके लिए मार्गदर्शन",
    "how.s2.body": "सांस, जर्नलिंग, सेल्फ-केयर जैसी गतिविधियां आपके लक्ष्यों से मेल खाती हैं।",
    "how.s3.title": "इनसाइट्स के साथ बढ़ें",
    "how.s3.body": "सरल एनालिटिक्स प्रगति दिखाते हैं ताकि आप जीतें मना सकें।",
    "trust.title": "विश्वास व सुरक्षा",
    "trust.1.title": "विशेषज्ञ निगरानी",
    "trust.1.body": "सलाहकार सामग्री की समीक्षा करते हैं। संकट में मानव सहयोग मिलता है।",
    "trust.2.title": "डेटा पारदर्शिता",
    "trust.2.body": "पारदर्शी मॉडल। आप अपने डेटा पर नियंत्रण रखते हैं।",
    "trust.3.title": "सुलभ डिज़ाइन",
    "trust.3.body": "सुलभता: उच्च कंट्रास्ट, स्क्रीन-रीडर फ्रेंडली।",
    "solutions.schools.title": "स्कूलों और NGOs के लिए",
    "solutions.schools.desc": "काउंसलर्स और मेंटर्स के लिए एक सहायक तैनात करें। एकत्रित और गुमनाम जानकारियाँ आपकी टीम को थकाए बिना अधिक छात्रों की मदद करने में सहायक होती हैं।",
    "solutions.families.title": "परिवारों के लिए",
    "solutions.families.desc": "घर पर स्वस्थ दिनचर्या बनाएँ—रिमाइंडर, साझा चेक-इन और किशोरों व युवाओं के लिए उपयुक्त सामग्री के साथ।",
    "activities.title": "निर्देशित गतिविधियाँ खोजें",
    "activities.subtitle": "मानसिक स्वास्थ्य यात्रा का समर्थन करने के लिए माइंडफुलनेस व्यायाम, जर्नलिंग प्रॉम्प्ट्स और सेल्फ-केयर गाइड्स खोजें।",
    "activities.breathing.title": "साँस लें और रीसेट करें",
    "activities.breathing.desc": "शांत लय के साथ साँस को समन्वयित करें ताकि पल में शांति मिले।",
    "activities.journal.title": "अपने विचार लिखें",
    "activities.journal.desc": "भावनाओं को समझने और स्पष्टता पाने के लिए निर्देशित प्रॉम्प्ट्स पर विचार करें।",
    "activities.selfcare.title": "सेल्फ-केयर गाइड्स",
    "activities.selfcare.desc": "दैनिक कल्याण और सेल्फ-केयर रूटीन के लिए क्यूरेटेड टिप्स और माइक्रो-कंटेंट।",
    "activities.cta": "और गतिविधियाँ खोजें",
  },
  hinglish: {
    "hero.title": "Human support, AI ke scale par",
    "hero.desc": "Saharathi AI young minds ko stress, anxiety aur uncertainty se guide karta hai — private, 24/7 support, culturally inclusive design ke saath.",
    "hero.cta": "Get Started",
    "hero.anonymous": "Koi account nahi chahiye – get started aur sab features anonymously use karo.",
    "hero.b1": "Secure & private",
    "hero.b2": "Gen Z ke liye banaya",
    "hero.b3": "24/7 available",
    "mood.title": "Aaj aap kaisa feel kar rahe ho?",
    "mood.subtitle": "Slider ko drag karo apna mood select karne ke liye, phir submit karo.",
    "mood.submit": "Submit",
    "mood.saved": "Saved ✅",
    "mood.analytics": "Mood Analytics",
    "mood.notePh": "Note add karo (optional)",
    "mission.1.title": "Proactive support",
    "mission.1.body": "Daily check-ins se early stress detect hota hai aur helpful steps milte hain.",
    "mission.2.title": "Private by design",
    "mission.2.body": "Aapki conversations encrypted hain aur aapke control mein.",
    "mission.3.title": "Inclusive guidance",
    "mission.3.body": "Culture-aware prompts har user ko support feel karne mein madad karte hain.",
    "how.title": "Kaise kaam karta hai",
    "how.s1.title": "Share & reflect",
    "how.s1.body": "Safe space mein baat karo. Pehle hum sunte hain, phir softly guide karte hain.",
    "how.s2.title": "Tailored guidance",
    "how.s2.body": "Exercises milti hain jo aapke goals ke match hoti hain — breathing, journaling, self-care.",
    "how.s3.title": "Grow with insights",
    "how.s3.body": "Progress trends dekho aur small wins celebrate karo.",
    "trust.title": "Trust & Safety",
    "trust.1.title": "Expert Oversight",
    "trust.1.body": "Advisors content check karte hain. Agar crisis ho toh human help tak escalate hota hai.",
    "trust.2.title": "Data Transparency",
    "trust.2.body": "Model transparent hai. Aap apne data pe kabhi bhi control kar sakte ho.",
    "trust.3.title": "Accessible Design",
    "trust.3.body": "Accessibility ensured hai: high contrast aur screen-reader friendly.",
    "solutions.schools.title": "Schools aur NGOs ke liye",
    "solutions.schools.desc": "Counsellors aur mentors ke liye ek co-pilot deploy karo. Aggregated aur anonymized insights se aap zyada students ko support kar sakte ho bina teams ko burnout kiye.",
    "solutions.families.title": "Families ke liye",
    "solutions.families.desc": "Ghar par healthy routines banao—reminders, shared check-ins, aur teens aur young adults ke liye age-aware content ke sath.",
    "activities.title": "Guided Activities Explore Karo",
    "activities.subtitle": "Mental wellness journey ke liye mindfulness exercises, journaling prompts, aur self-care guides discover karo.",
    "activities.breathing.title": "Saans Lo aur Reset Karo",
    "activities.breathing.desc": "Calm rhythm ke saath saans sync karo taaki moment mein peace mile.",
    "activities.journal.title": "Apne Thoughts Journal Karo",
    "activities.journal.desc": "Emotions process karne aur clarity pane ke liye guided prompts pe reflect karo.",
    "activities.selfcare.title": "Self-Care Guides",
    "activities.selfcare.desc": "Daily wellness aur self-care routines ke liye curated tips aur micro-content.",
    "activities.cta": "Aur Activities Discover Karo",
  }
};

const MOOD_LEVELS = {
  en: ["😣 Stressed", "😔 Sad", "😐 Okay", "🙂 Good", "😊 Great"],
  hi: ["😣 बहुत तनाव", "😔 उदास", "😐 ठीक-ठाक", "🙂 अच्छा", "😊 बहुत अच्छा"],
  hinglish: ["😣 Tension", "😔 Udaas", "😐 Theek-Thaak", "🙂 Accha", "😊 Bahut accha"],
};

const MOOD_VALUES = [0, 1, 2, 3, 4];

let currentLang = "en";

function applyLanguage(lang) {
  currentLang = lang;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (i18n[lang] && i18n[lang][key]) {
      el.innerText = i18n[lang][key];
    }
  });
  document.querySelectorAll("[data-i18n-ph]").forEach(el => {
    const key = el.getAttribute("data-i18n-ph");
    if (i18n[lang] && i18n[lang][key]) {
      el.placeholder = i18n[lang][key];
    }
  });
  updateMoodLabel(document.getElementById("moodSlider")?.value);
}

function updateMoodLabel(value) {
  const index = MOOD_VALUES.indexOf(parseInt(value));
  if (index !== -1) {
    const [emoji, label] = MOOD_LEVELS[currentLang][index].split(" ");
    document.getElementById("moodEmoji").innerText = emoji;
    document.getElementById("moodLabel").innerText = label;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Mobile Menu Toggle
  const menuBtn = document.getElementById("menuBtn");
  const mobileNav = document.getElementById("mobileNav");
  menuBtn?.addEventListener("click", () => mobileNav.classList.toggle("hidden"));

  // Navbar Elevation on Scroll
  const nav = document.getElementById("nav");
  const onScroll = () => {
    nav.classList.toggle("shadow-[0_4px_24px_rgba(0,0,0,0.22)]", window.scrollY > 8);
  };
  window.addEventListener("scroll", onScroll);
  onScroll();

  // Hero Fade
  const hero = document.querySelector("section");
  const updateHeroFade = () => {
    const rect = hero.getBoundingClientRect();
    const viewportH = window.innerHeight || 1;
    const progress = Math.min(1, Math.max(0, (viewportH - rect.top) / (rect.height * 0.85)));
    document.documentElement.style.setProperty("--hero-fade", progress.toFixed(3));
  };
  window.addEventListener("scroll", updateHeroFade);
  window.addEventListener("resize", updateHeroFade);
  updateHeroFade();

  // Mood Slider
  const moodSlider = document.getElementById("moodSlider");
  moodSlider?.addEventListener("input", () => updateMoodLabel(moodSlider.value));

  // Mood Submission
  const moodSubmit = document.getElementById("moodSubmit");
  const moodSaved = document.getElementById("moodSaved");
  const moodAnalytics = document.getElementById("moodAnalytics");
  const moodNotes = document.getElementById("moodNotes");
  moodSubmit?.addEventListener("click", () => {
    const moodValue = parseInt(moodSlider.value);
    const note = moodNotes.value.trim();
    const timestamp = new Date().toISOString();
    moods.push({ mood: moodValue, note, timestamp });
    localStorage.setItem("moods", JSON.stringify(moods));
    moodSaved.classList.remove("hidden");
    setTimeout(() => moodSaved.classList.add("hidden"), 2000);
    if (moods.length >= 3) moodAnalytics.classList.remove("hidden");
  });

  // Language Switcher
  const langSwitcher = document.getElementById("langSwitcher");
  const langSwitcherMobile = document.getElementById("langSwitcherMobile");
  langSwitcher?.addEventListener("change", () => applyLanguage(langSwitcher.value));
  langSwitcherMobile?.addEventListener("change", () => applyLanguage(langSwitcherMobile.value));

  // Initialize Language
  applyLanguage(currentLang);
});