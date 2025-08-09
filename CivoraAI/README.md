# Civora AI - Unbiased News App

A React Native mobile application that delivers unbiased news through AI-powered bias detection and content synthesis.

## 🎯 Mission

Civora AI believes in presenting news as it is, without political bias or distortion. Our AI technology analyzes multiple sources to deliver balanced, unbiased reporting.

## ✨ Features

### Core Features
- **AI-Powered Bias Detection**: Advanced NLP algorithms quantify ideological bias
- **Multi-Source Synthesis**: Combines perspectives from diverse news sources
- **Personalized Feed**: Tailored content based on user interests and preferences
- **Language Style Customization**: Choose from Gen Z, Professional, Informative, or Friendly styles
- **Bias Indicators**: Visual indicators showing bias levels for transparency

### User Experience
- **Sleek Design**: Modern, clean interface with intuitive navigation
- **Category Filtering**: Browse news by Politics, Technology, Sports, Finance, World Events
- **Bookmark & Share**: Save articles and share with others
- **Source Transparency**: View all sources used in article synthesis
- **Reading Preferences**: Customize your news consumption experience

## 🚀 Getting Started

### Prerequisites
- Node.js (v16 or higher)
- npm or yarn
- Expo CLI
- iOS Simulator (for iOS development) or Android Studio (for Android development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CivoraAI
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

4. **Run on your preferred platform**
   ```bash
   # For iOS
   npm run ios
   
   # For Android
   npm run android
   
   # For web
   npm run web
   ```

## 📱 App Structure

```
src/
├── screens/
│   ├── HomeScreen.tsx          # Main news feed
│   ├── ExploreScreen.tsx       # Trending topics and AI content
│   ├── ProfileScreen.tsx       # User preferences and settings
│   ├── ArticleScreen.tsx       # Article detail view
│   └── OnboardingScreen.tsx    # Welcome and setup flow
├── types/
│   └── index.ts               # TypeScript interfaces
└── components/                # Reusable UI components
```

## 🎨 Design System

### Colors
- **Primary Blue**: `#2563eb` - Main brand color
- **Success Green**: `#10b981` - Low bias indicators
- **Warning Orange**: `#f59e0b` - Medium bias indicators
- **Error Red**: `#ef4444` - High bias indicators
- **Neutral Grays**: Various shades for text and backgrounds

### Typography
- **Headings**: Bold, large text for titles
- **Body**: Readable, medium-sized text for content
- **Captions**: Small text for metadata and labels

## 🔧 Technology Stack

- **React Native**: Cross-platform mobile development
- **Expo**: Development platform and tools
- **TypeScript**: Type-safe JavaScript
- **React Navigation**: Navigation between screens
- **Expo Vector Icons**: Icon library

## 📊 Key Features Explained

### Bias Detection
Our AI analyzes articles from multiple sources and assigns bias scores:
- **Low Bias (0-0.1)**: Green indicator
- **Medium Bias (0.1-0.2)**: Orange indicator  
- **High Bias (0.2+)**: Red indicator

### Content Synthesis
1. **Source Gathering**: Collect articles from diverse news outlets
2. **Bias Analysis**: Quantify ideological bias using NLP
3. **Content Synthesis**: Generate balanced, unbiased articles
4. **Source Attribution**: Display all sources used in synthesis

### Personalization
- **Interest Selection**: Choose from Politics, Technology, Sports, Finance, World Events
- **Language Style**: Gen Z, Professional, Informative, or Friendly
- **Reading Preferences**: Dark mode, notifications, and more

## 🎯 Future Enhancements

Based on the PRD, planned features include:
- **Video Content**: AI-generated and bias-filtered videos
- **Short-form Content**: "Scoops" similar to social media stories
- **Advanced Notifications**: Personalized story recommendations
- **Enhanced AI**: More sophisticated bias detection algorithms
- **Source Expansion**: Integration with more news outlets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with React Native and Expo
- Icons from Expo Vector Icons
- Design inspired by modern news applications
- Mission inspired by the need for unbiased journalism

---

**Civora AI** - News as it is. 📰✨ 