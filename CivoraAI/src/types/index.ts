export interface Article {
  id: string;
  title: string;
  content: string;
  summary: string;
  imageUrl?: string;
  category: string;
  biasScore: number;
  sources: Source[];
  publishedAt: string;
  readTime: number;
  isBookmarked: boolean;
  userStyle: string;
}

export interface Source {
  name: string;
  biasScore: number;
  url: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  interests: string[];
  languageStyle: string;
  preferences: UserPreferences;
}

export interface UserPreferences {
  darkMode: boolean;
  notifications: boolean;
  languageStyle: 'Gen Z' | 'Professional' | 'Informative' | 'Friendly';
  interests: string[];
}

export interface Category {
  id: string;
  name: string;
  icon: string;
  color: string;
}

export interface BiasIndicator {
  score: number;
  level: 'Low' | 'Medium' | 'High';
  color: string;
} 