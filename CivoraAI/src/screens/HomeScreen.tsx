import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  RefreshControl,
  FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Article, Category } from '../types';

const mockArticles: Article[] = [
  {
    id: '1',
    title: 'Federal Reserve Announces New Interest Rate Policy',
    content: 'The Federal Reserve has announced a new interest rate policy that aims to balance economic growth with inflation control...',
    summary: 'Fed introduces balanced approach to monetary policy',
    category: 'Finance',
    biasScore: 0.15,
    sources: [
      { name: 'Reuters', biasScore: 0.1, url: 'https://reuters.com' },
      { name: 'Bloomberg', biasScore: 0.2, url: 'https://bloomberg.com' },
    ],
    publishedAt: '2024-01-15T10:30:00Z',
    readTime: 3,
    isBookmarked: false,
    userStyle: 'Professional',
  },
  {
    id: '2',
    title: 'Climate Summit Reaches Historic Agreement',
    content: 'World leaders have reached a historic agreement on climate change measures during the latest international summit...',
    summary: 'Global climate agreement sets new emission targets',
    category: 'World Events',
    biasScore: 0.08,
    sources: [
      { name: 'AP News', biasScore: 0.05, url: 'https://apnews.com' },
      { name: 'BBC', biasScore: 0.12, url: 'https://bbc.com' },
    ],
    publishedAt: '2024-01-15T09:15:00Z',
    readTime: 4,
    isBookmarked: true,
    userStyle: 'Informative',
  },
  {
    id: '3',
    title: 'Tech Giants Face New AI Regulations',
    content: 'Major technology companies are facing new regulations regarding artificial intelligence development and deployment...',
    summary: 'New AI regulations impact major tech companies',
    category: 'Technology',
    biasScore: 0.22,
    sources: [
      { name: 'TechCrunch', biasScore: 0.25, url: 'https://techcrunch.com' },
      { name: 'The Verge', biasScore: 0.18, url: 'https://theverge.com' },
    ],
    publishedAt: '2024-01-15T08:45:00Z',
    readTime: 5,
    isBookmarked: false,
    userStyle: 'Gen Z',
  },
];

const categories: Category[] = [
  { id: '1', name: 'Politics', icon: 'flag', color: '#ef4444' },
  { id: '2', name: 'Technology', icon: 'laptop', color: '#3b82f6' },
  { id: '3', name: 'Sports', icon: 'football', color: '#10b981' },
  { id: '4', name: 'Finance', icon: 'trending-up', color: '#f59e0b' },
  { id: '5', name: 'World Events', icon: 'globe', color: '#8b5cf6' },
];

const BiasIndicator: React.FC<{ score: number }> = ({ score }) => {
  const getBiasColor = (score: number) => {
    if (score < 0.1) return '#10b981';
    if (score < 0.2) return '#f59e0b';
    return '#ef4444';
  };

  const getBiasLevel = (score: number) => {
    if (score < 0.1) return 'Low';
    if (score < 0.2) return 'Medium';
    return 'High';
  };

  return (
    <View style={[styles.biasIndicator, { backgroundColor: getBiasColor(score) }]}>
      <Text style={styles.biasText}>{getBiasLevel(score)} Bias</Text>
    </View>
  );
};

const ArticleCard: React.FC<{ article: Article; onPress: () => void }> = ({ article, onPress }) => {
  return (
    <TouchableOpacity style={styles.articleCard} onPress={onPress}>
      <View style={styles.articleHeader}>
        <Text style={styles.articleCategory}>{article.category}</Text>
        <BiasIndicator score={article.biasScore} />
      </View>
      
      <Text style={styles.articleTitle} numberOfLines={2}>
        {article.title}
      </Text>
      
      <Text style={styles.articleSummary} numberOfLines={2}>
        {article.summary}
      </Text>
      
      <View style={styles.articleFooter}>
        <View style={styles.articleMeta}>
          <Ionicons name="time-outline" size={14} color="#64748b" />
          <Text style={styles.articleMetaText}>{article.readTime} min read</Text>
        </View>
        
        <View style={styles.articleActions}>
          <TouchableOpacity style={styles.actionButton}>
            <Ionicons 
              name={article.isBookmarked ? "bookmark" : "bookmark-outline"} 
              size={20} 
              color="#64748b" 
            />
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="share-outline" size={20} color="#64748b" />
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const CategoryButton: React.FC<{ category: Category; isActive: boolean; onPress: () => void }> = ({ 
  category, isActive, onPress 
}) => {
  return (
    <TouchableOpacity 
      style={[styles.categoryButton, isActive && styles.categoryButtonActive]} 
      onPress={onPress}
    >
      <Ionicons 
        name={category.icon as any} 
        size={20} 
        color={isActive ? '#ffffff' : category.color} 
      />
      <Text style={[styles.categoryText, isActive && styles.categoryTextActive]}>
        {category.name}
      </Text>
    </TouchableOpacity>
  );
};

const HomeScreen: React.FC = ({ navigation }: any) => {
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const onRefresh = () => {
    setRefreshing(true);
    // Simulate refresh
    setTimeout(() => setRefreshing(false), 1000);
  };

  const handleArticlePress = (article: Article) => {
    navigation.navigate('Article', { article });
  };

  const filteredArticles = selectedCategory 
    ? mockArticles.filter(article => article.category === selectedCategory)
    : mockArticles;

  return (
    <View style={styles.container}>
      {/* Welcome Section */}
      <View style={styles.welcomeSection}>
        <Text style={styles.welcomeText}>Good morning, User</Text>
        <Text style={styles.welcomeSubtext}>Here's your unbiased news feed</Text>
      </View>

      {/* Categories */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        style={styles.categoriesContainer}
        contentContainerStyle={styles.categoriesContent}
      >
        <CategoryButton
          category={{ id: 'all', name: 'All', icon: 'grid', color: '#64748b' }}
          isActive={!selectedCategory}
          onPress={() => setSelectedCategory(null)}
        />
        {categories.map(category => (
          <CategoryButton
            key={category.id}
            category={category}
            isActive={selectedCategory === category.name}
            onPress={() => setSelectedCategory(category.name)}
          />
        ))}
      </ScrollView>

      {/* Articles Feed */}
      <FlatList
        data={filteredArticles}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <ArticleCard article={item} onPress={() => handleArticlePress(item)} />
        )}
        contentContainerStyle={styles.articlesContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  welcomeSection: {
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#ffffff',
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 4,
  },
  welcomeSubtext: {
    fontSize: 14,
    color: '#64748b',
  },
  categoriesContainer: {
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  categoriesContent: {
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  categoryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 12,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    backgroundColor: '#ffffff',
  },
  categoryButtonActive: {
    backgroundColor: '#2563eb',
    borderColor: '#2563eb',
  },
  categoryText: {
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '500',
    color: '#64748b',
  },
  categoryTextActive: {
    color: '#ffffff',
  },
  articlesContainer: {
    padding: 20,
  },
  articleCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  articleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  articleCategory: {
    fontSize: 12,
    fontWeight: '600',
    color: '#2563eb',
    textTransform: 'uppercase',
  },
  biasIndicator: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  biasText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#ffffff',
  },
  articleTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 8,
    lineHeight: 24,
  },
  articleSummary: {
    fontSize: 14,
    color: '#64748b',
    lineHeight: 20,
    marginBottom: 16,
  },
  articleFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  articleMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  articleMetaText: {
    fontSize: 12,
    color: '#64748b',
    marginLeft: 4,
  },
  articleActions: {
    flexDirection: 'row',
  },
  actionButton: {
    marginLeft: 16,
  },
});

export default HomeScreen; 