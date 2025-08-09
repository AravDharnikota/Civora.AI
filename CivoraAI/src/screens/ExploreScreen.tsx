import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Article, Category } from '../types';

const mockTrendingTopics = [
  { id: '1', title: 'AI Regulation', count: 1247, biasScore: 0.12 },
  { id: '2', title: 'Climate Policy', count: 892, biasScore: 0.08 },
  { id: '3', title: 'Economic Recovery', count: 654, biasScore: 0.15 },
  { id: '4', title: 'Space Exploration', count: 432, biasScore: 0.05 },
  { id: '5', title: 'Healthcare Reform', count: 321, biasScore: 0.18 },
];

const mockAIGenerated = [
  {
    id: '1',
    title: 'AI-Generated: Global Economic Outlook 2024',
    summary: 'Synthesized from 15+ sources with minimal bias',
    biasScore: 0.03,
    sources: 15,
  },
  {
    id: '2',
    title: 'AI-Generated: Climate Change Consensus Report',
    summary: 'Balanced analysis from leading environmental sources',
    biasScore: 0.05,
    sources: 12,
  },
];

const TrendingTopicCard: React.FC<{ topic: any; onPress: () => void }> = ({ topic, onPress }) => {
  const getBiasColor = (score: number) => {
    if (score < 0.1) return '#10b981';
    if (score < 0.2) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <TouchableOpacity style={styles.topicCard} onPress={onPress}>
      <View style={styles.topicHeader}>
        <Text style={styles.topicTitle}>{topic.title}</Text>
        <View style={[styles.biasBadge, { backgroundColor: getBiasColor(topic.biasScore) }]}>
          <Text style={styles.biasBadgeText}>Low Bias</Text>
        </View>
      </View>
      <View style={styles.topicMeta}>
        <Ionicons name="trending-up" size={16} color="#64748b" />
        <Text style={styles.topicCount}>{topic.count} articles</Text>
      </View>
    </TouchableOpacity>
  );
};

const AIGeneratedCard: React.FC<{ article: any; onPress: () => void }> = ({ article, onPress }) => {
  return (
    <TouchableOpacity style={styles.aiCard} onPress={onPress}>
      <View style={styles.aiHeader}>
        <View style={styles.aiBadge}>
          <Ionicons name="sparkles" size={16} color="#8b5cf6" />
          <Text style={styles.aiBadgeText}>AI Generated</Text>
        </View>
        <View style={[styles.biasBadge, { backgroundColor: '#10b981' }]}>
          <Text style={styles.biasBadgeText}>Minimal Bias</Text>
        </View>
      </View>
      
      <Text style={styles.aiTitle}>{article.title}</Text>
      <Text style={styles.aiSummary}>{article.summary}</Text>
      
      <View style={styles.aiFooter}>
        <View style={styles.aiMeta}>
          <Ionicons name="library-outline" size={14} color="#64748b" />
          <Text style={styles.aiMetaText}>{article.sources} sources</Text>
        </View>
        <View style={styles.aiMeta}>
          <Ionicons name="shield-checkmark-outline" size={14} color="#64748b" />
          <Text style={styles.aiMetaText}>Verified</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const ExploreScreen: React.FC = ({ navigation }: any) => {
  const [selectedFilter, setSelectedFilter] = useState('all');

  const filters = [
    { id: 'all', name: 'All' },
    { id: 'trending', name: 'Trending' },
    { id: 'ai', name: 'AI Generated' },
    { id: 'analysis', name: 'Bias Analysis' },
  ];

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Explore</Text>
        <Text style={styles.headerSubtitle}>Discover unbiased news and insights</Text>
      </View>

      {/* Filters */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        style={styles.filtersContainer}
        contentContainerStyle={styles.filtersContent}
      >
        {filters.map(filter => (
          <TouchableOpacity
            key={filter.id}
            style={[
              styles.filterButton,
              selectedFilter === filter.id && styles.filterButtonActive
            ]}
            onPress={() => setSelectedFilter(filter.id)}
          >
            <Text style={[
              styles.filterText,
              selectedFilter === filter.id && styles.filterTextActive
            ]}>
              {filter.name}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Trending Topics */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Trending Topics</Text>
            <TouchableOpacity>
              <Text style={styles.seeAllText}>See all</Text>
            </TouchableOpacity>
          </View>
          
          <FlatList
            data={mockTrendingTopics}
            horizontal
            showsHorizontalScrollIndicator={false}
            renderItem={({ item }) => (
              <TrendingTopicCard 
                topic={item} 
                onPress={() => navigation.navigate('Article', { topic: item })}
              />
            )}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.topicsContainer}
          />
        </View>

        {/* AI Generated Content */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>AI Generated</Text>
            <Text style={styles.sectionSubtitle}>Synthesized from multiple sources</Text>
          </View>
          
          {mockAIGenerated.map(article => (
            <AIGeneratedCard
              key={article.id}
              article={article}
              onPress={() => navigation.navigate('Article', { article })}
            />
          ))}
        </View>

        {/* Bias Analysis */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Bias Analysis</Text>
            <Text style={styles.sectionSubtitle}>How we ensure unbiased reporting</Text>
          </View>
          
          <View style={styles.analysisCard}>
            <View style={styles.analysisHeader}>
              <Ionicons name="analytics-outline" size={24} color="#2563eb" />
              <Text style={styles.analysisTitle}>Our Process</Text>
            </View>
            
            <View style={styles.processSteps}>
              <View style={styles.processStep}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>1</Text>
                </View>
                <Text style={styles.stepText}>Gather articles from diverse sources</Text>
              </View>
              
              <View style={styles.processStep}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>2</Text>
                </View>
                <Text style={styles.stepText}>Analyze and quantify bias using NLP</Text>
              </View>
              
              <View style={styles.processStep}>
                <View style={styles.stepNumber}>
                  <Text style={styles.stepNumberText}>3</Text>
                </View>
                <Text style={styles.stepText}>Synthesize balanced, unbiased content</Text>
              </View>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#ffffff',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#64748b',
  },
  filtersContainer: {
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  filtersContent: {
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 12,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    backgroundColor: '#ffffff',
  },
  filterButtonActive: {
    backgroundColor: '#2563eb',
    borderColor: '#2563eb',
  },
  filterText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#64748b',
  },
  filterTextActive: {
    color: '#ffffff',
  },
  content: {
    flex: 1,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e293b',
  },
  sectionSubtitle: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  seeAllText: {
    fontSize: 14,
    color: '#2563eb',
    fontWeight: '500',
  },
  topicsContainer: {
    paddingHorizontal: 20,
  },
  topicCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginRight: 12,
    width: 200,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  topicHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  topicTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    flex: 1,
    marginRight: 8,
  },
  biasBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  biasBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#ffffff',
  },
  topicMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  topicCount: {
    fontSize: 12,
    color: '#64748b',
    marginLeft: 4,
  },
  aiCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 20,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  aiHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  aiBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  aiBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8b5cf6',
    marginLeft: 4,
  },
  aiTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 8,
  },
  aiSummary: {
    fontSize: 14,
    color: '#64748b',
    lineHeight: 20,
    marginBottom: 12,
  },
  aiFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  aiMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  aiMetaText: {
    fontSize: 12,
    color: '#64748b',
    marginLeft: 4,
  },
  analysisCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  analysisHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  analysisTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e293b',
    marginLeft: 8,
  },
  processSteps: {
    gap: 12,
  },
  processStep: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stepNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#2563eb',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  stepNumberText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#ffffff',
  },
  stepText: {
    fontSize: 14,
    color: '#64748b',
    flex: 1,
  },
});

export default ExploreScreen; 