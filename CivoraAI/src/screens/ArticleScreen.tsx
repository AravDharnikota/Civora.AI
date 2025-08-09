import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Share,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Article, Source } from '../types';

const mockArticle: Article = {
  id: '1',
  title: 'Federal Reserve Announces New Interest Rate Policy',
  content: `The Federal Reserve has announced a new interest rate policy that aims to balance economic growth with inflation control. This comprehensive approach represents a significant shift in monetary policy strategy.

The new policy framework incorporates multiple economic indicators, including employment rates, inflation expectations, and GDP growth projections. Federal Reserve Chair Jerome Powell emphasized the importance of maintaining price stability while supporting maximum employment.

"Our approach is data-dependent and forward-looking," Powell stated during the announcement. "We will continue to monitor economic conditions and adjust our policy stance as needed to achieve our dual mandate."

The policy announcement comes amid ongoing economic recovery efforts and concerns about inflationary pressures. Market analysts have been closely watching for signals about the Fed's future direction, particularly regarding the pace of interest rate adjustments.

Key aspects of the new policy include:
• Flexible average inflation targeting
• Enhanced forward guidance
• Regular policy reviews and adjustments
• Transparent communication with markets

The announcement has already had immediate effects on financial markets, with bond yields adjusting to reflect the new policy framework. Economists expect this approach to provide greater clarity for businesses and consumers making long-term financial decisions.`,
  summary: 'Fed introduces balanced approach to monetary policy',
  category: 'Finance',
  biasScore: 0.15,
  sources: [
    { name: 'Reuters', biasScore: 0.1, url: 'https://reuters.com' },
    { name: 'Bloomberg', biasScore: 0.2, url: 'https://bloomberg.com' },
    { name: 'AP News', biasScore: 0.05, url: 'https://apnews.com' },
  ],
  publishedAt: '2024-01-15T10:30:00Z',
  readTime: 3,
  isBookmarked: false,
  userStyle: 'Professional',
};

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
      <Ionicons name="shield-checkmark-outline" size={16} color="#ffffff" />
      <Text style={styles.biasText}>{getBiasLevel(score)} Bias</Text>
    </View>
  );
};

const SourceCard: React.FC<{ source: Source }> = ({ source }) => {
  const getBiasColor = (score: number) => {
    if (score < 0.1) return '#10b981';
    if (score < 0.2) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <View style={styles.sourceCard}>
      <View style={styles.sourceHeader}>
        <Text style={styles.sourceName}>{source.name}</Text>
        <View style={[styles.sourceBias, { backgroundColor: getBiasColor(source.biasScore) }]}>
          <Text style={styles.sourceBiasText}>
            {source.biasScore < 0.1 ? 'Low' : source.biasScore < 0.2 ? 'Medium' : 'High'} Bias
          </Text>
        </View>
      </View>
      <Text style={styles.sourceUrl}>{source.url}</Text>
    </View>
  );
};

const ArticleScreen: React.FC = ({ route, navigation }: any) => {
  const { article } = route.params || { article: mockArticle };
  const [isBookmarked, setIsBookmarked] = useState(article.isBookmarked);

  const handleShare = async () => {
    try {
      await Share.share({
        message: `Check out this unbiased article: ${article.title}`,
        title: article.title,
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Article Header */}
        <View style={styles.articleHeader}>
          <View style={styles.articleMeta}>
            <Text style={styles.articleCategory}>{article.category}</Text>
            <BiasIndicator score={article.biasScore} />
          </View>
          
          <Text style={styles.articleTitle}>{article.title}</Text>
          
          <View style={styles.articleInfo}>
            <View style={styles.infoItem}>
              <Ionicons name="time-outline" size={16} color="#64748b" />
              <Text style={styles.infoText}>{article.readTime} min read</Text>
            </View>
            <View style={styles.infoItem}>
              <Ionicons name="calendar-outline" size={16} color="#64748b" />
              <Text style={styles.infoText}>{formatDate(article.publishedAt)}</Text>
            </View>
          </View>
        </View>

        {/* Article Content */}
        <View style={styles.articleContent}>
          <Text style={styles.contentText}>{article.content}</Text>
        </View>

        {/* AI Generation Notice */}
        <View style={styles.aiNotice}>
          <View style={styles.aiNoticeHeader}>
            <Ionicons name="sparkles" size={20} color="#8b5cf6" />
            <Text style={styles.aiNoticeTitle}>AI Generated Content</Text>
          </View>
          <Text style={styles.aiNoticeText}>
            This article was synthesized from multiple sources using our bias-reduction algorithms. 
            We've analyzed {article.sources.length} different perspectives to provide you with balanced, 
            unbiased reporting.
          </Text>
        </View>

        {/* Sources */}
        <View style={styles.sourcesSection}>
          <Text style={styles.sourcesTitle}>Sources Used</Text>
          <Text style={styles.sourcesSubtitle}>
            These sources were analyzed and synthesized to create this unbiased article
          </Text>
          
                     {article.sources.map((source: Source, index: number) => (
             <SourceCard key={index} source={source} />
           ))}
        </View>

        {/* Related Articles */}
        <View style={styles.relatedSection}>
          <Text style={styles.relatedTitle}>Related Articles</Text>
          <View style={styles.relatedCard}>
            <Text style={styles.relatedCardTitle}>Economic Policy Changes</Text>
            <Text style={styles.relatedCardSummary}>
              Analysis of recent economic policy developments and their implications
            </Text>
            <View style={styles.relatedCardMeta}>
              <Text style={styles.relatedCardCategory}>Finance</Text>
              <Text style={styles.relatedCardTime}>2 min read</Text>
            </View>
          </View>
        </View>
      </ScrollView>

      {/* Action Bar */}
      <View style={styles.actionBar}>
        <TouchableOpacity style={styles.actionButton} onPress={handleBookmark}>
          <Ionicons 
            name={isBookmarked ? "bookmark" : "bookmark-outline"} 
            size={24} 
            color={isBookmarked ? "#2563eb" : "#64748b"} 
          />
          <Text style={[styles.actionText, isBookmarked && styles.actionTextActive]}>
            {isBookmarked ? 'Saved' : 'Save'}
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
          <Ionicons name="share-outline" size={24} color="#64748b" />
          <Text style={styles.actionText}>Share</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.actionButton}>
          <Ionicons name="chatbubble-outline" size={24} color="#64748b" />
          <Text style={styles.actionText}>Discuss</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  content: {
    flex: 1,
  },
  articleHeader: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  articleMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  articleCategory: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2563eb',
    textTransform: 'uppercase',
  },
  biasIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  biasText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
    marginLeft: 4,
  },
  articleTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1e293b',
    lineHeight: 32,
    marginBottom: 16,
  },
  articleInfo: {
    flexDirection: 'row',
    gap: 16,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  infoText: {
    fontSize: 14,
    color: '#64748b',
    marginLeft: 4,
  },
  articleContent: {
    padding: 20,
  },
  contentText: {
    fontSize: 16,
    lineHeight: 24,
    color: '#374151',
  },
  aiNotice: {
    margin: 20,
    padding: 16,
    backgroundColor: '#f8fafc',
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#8b5cf6',
  },
  aiNoticeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  aiNoticeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginLeft: 8,
  },
  aiNoticeText: {
    fontSize: 14,
    color: '#64748b',
    lineHeight: 20,
  },
  sourcesSection: {
    padding: 20,
    backgroundColor: '#f8fafc',
  },
  sourcesTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 4,
  },
  sourcesSubtitle: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 16,
  },
  sourceCard: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  sourceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  sourceName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e293b',
  },
  sourceBias: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  sourceBiasText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#ffffff',
  },
  sourceUrl: {
    fontSize: 12,
    color: '#64748b',
  },
  relatedSection: {
    padding: 20,
  },
  relatedTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 12,
  },
  relatedCard: {
    backgroundColor: '#f8fafc',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  relatedCardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 8,
  },
  relatedCardSummary: {
    fontSize: 14,
    color: '#64748b',
    lineHeight: 20,
    marginBottom: 12,
  },
  relatedCardMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  relatedCardCategory: {
    fontSize: 12,
    fontWeight: '600',
    color: '#2563eb',
    textTransform: 'uppercase',
  },
  relatedCardTime: {
    fontSize: 12,
    color: '#64748b',
  },
  actionBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 16,
    paddingHorizontal: 20,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  actionButton: {
    alignItems: 'center',
  },
  actionText: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 4,
  },
  actionTextActive: {
    color: '#2563eb',
  },
});

export default ArticleScreen; 