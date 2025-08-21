import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Globe, ShieldCheck, Heart } from "lucide-react";

export default function OnboardingWelcome() {
  const [step, setStep] = useState(0);

  const slides = [
    {
      icon: <Heart className="w-12 h-12 text-pink-500" />,
      title: "Your Wellness Buddy",
      description:
        "An empathetic AI companion built to listen, support, and guide you through life’s ups and downs.",
    },
    {
      icon: <Globe className="w-12 h-12 text-blue-500" />,
      title: "Culturally Aware & Multilingual",
      description:
        "Chat in English, Hindi, or Hinglish. Our AI understands your language and context.",
    },
    {
      icon: <ShieldCheck className="w-12 h-12 text-green-500" />,
      title: "Confidential & Safe",
      description:
        "Your conversations and journals are private, encrypted, and never shared with anyone.",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-between bg-gradient-to-b from-pink-100 via-white to-blue-100 p-6">
      <div className="flex-1 flex flex-col items-center justify-center text-center">
        <motion.div
          key={step}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <Card className="rounded-2xl shadow-lg p-6">
            <CardContent className="flex flex-col items-center space-y-6">
              {slides[step].icon}
              <h2 className="text-2xl font-semibold text-gray-800">
                {slides[step].title}
              </h2>
              <p className="text-gray-600 text-base leading-relaxed">
                {slides[step].description}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="flex justify-between items-center w-full max-w-md py-4">
        {step > 0 ? (
          <Button variant="ghost" onClick={() => setStep(step - 1)}>
            Back
          </Button>
        ) : (
          <div></div>
        )}

        {step < slides.length - 1 ? (
          <Button onClick={() => setStep(step + 1)}>Next</Button>
        ) : (
          <Button className="bg-pink-500 hover:bg-pink-600 text-white rounded-full px-6 py-2 text-lg">
            Get Started
          </Button>
        )}
      </div>
    </div>
  );
}
