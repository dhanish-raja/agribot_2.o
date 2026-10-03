import { 
  Sprout, 
  Bug, 
  FlaskConical, 
  ShieldAlert, 
  Sparkles,
  ArrowRight
} from "lucide-react";
import { User } from "../types";

interface WelcomeHeroProps {
  user: User;
  onSelectPrompt: (prompt: string, crop?: string) => void;
}

export const WelcomeHero = ({ user, onSelectPrompt }: WelcomeHeroProps) => {
  const starterCards = [
    {
      category: "Disease Diagnostics",
      crop: "rice",
      cropName: "Rice",
      icon: <ShieldAlert size={20} className="card-icon-alert" />,
      title: "Bacterial Blight in Rice",
      prompt: "How to identify and control Bacterial Leaf Blight in rice?",
      description: "Symptoms, streptocycline dosages, and water drainage practices."
    },
    {
      category: "Orchard Nutrition",
      crop: "coconut",
      cropName: "Coconut",
      icon: <FlaskConical size={20} className="card-icon-flask" />,
      title: "Fertilizer Schedule for Palms",
      prompt: "What is the recommended NPK and organic fertilizer schedule for mature coconut trees?",
      description: "Basal application, micronutrients (Boron/Magnesium), and organic compost."
    },
    {
      category: "Crop Protection",
      crop: "sugarcane",
      cropName: "Sugarcane",
      icon: <Bug size={20} className="card-icon-bug" />,
      title: "Red Rot & Borer Control",
      prompt: "How to identify and treat Red Rot and Early Shoot Borer in sugarcane?",
      description: "Resistant sett treatment, biological agents (Trichogramma), and chemical spray."
    },
    {
      category: "Pest Management",
      crop: "mango",
      cropName: "Mango",
      icon: <Sprout size={20} className="card-icon-sprout" />,
      title: "Fruit Fly & Powdery Mildew",
      prompt: "What are the preventive measures and spray schedule for mango fruit fly and powdery mildew?",
      description: "Pheromone traps, sanitation, and wettable sulfur application."
    }
  ];

  return (
    <div className="welcome-hero-container">
      <div className="hero-banner">
        <div className="hero-badge">
          <Sparkles size={14} />
          <span>Enterprise Agronomy Copilot</span>
        </div>
        <h2 className="hero-heading">
          Namaste, {user.name.split(" ")[0]}! 🌿
        </h2>
        <p className="hero-subtext">
          What crop or agronomy challenge can I help you resolve today? Ask anything about diagnosis, nutrient management, or spray dosages.
        </p>
      </div>

      <div className="starter-cards-grid">
        {starterCards.map((card, idx) => (
          <div
            key={idx}
            className="starter-card"
            onClick={() => onSelectPrompt(card.prompt, card.crop)}
          >
            <div className="card-top">
              <span className="card-category-badge">{card.cropName} • {card.category}</span>
              <div className="card-icon-wrap">{card.icon}</div>
            </div>
            <h4 className="card-title">{card.title}</h4>
            <p className="card-desc">{card.description}</p>
            <div className="card-action-row">
              <span className="ask-btn-text">Ask AgriBot</span>
              <ArrowRight size={14} className="arrow-icon" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
