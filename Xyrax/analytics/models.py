from django.db import models


class Post(models.Model):
    session_key = models.CharField(max_length=120, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Inputs
    likes = models.IntegerField(default=0)
    saves = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    follows = models.IntegerField(default=0)
    profile_visits = models.IntegerField(default=0)
    caption_length = models.IntegerField(default=0)
    hashtags = models.IntegerField(default=0)
    reposts = models.IntegerField(default=0)

    # Outputs
    predicted_impressions = models.IntegerField(default=0)
    viral_score = models.FloatField(default=0)
    eng_rate = models.FloatField(default=0)
    follow_rate = models.FloatField(default=0)
    ai_viral_label = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ['created_at']

    def to_dict(self):
        return {
            'likes': self.likes,
            'saves': self.saves,
            'comments': self.comments,
            'shares': self.shares,
            'follows': self.follows,
            'profile_visits': self.profile_visits,
            'caption_length': self.caption_length,
            'hashtags': self.hashtags,
            'reposts': self.reposts,
            'predicted_impressions': self.predicted_impressions,
            'viral_score': self.viral_score,
            'eng_rate': self.eng_rate,
            'follow_rate': self.follow_rate,
            'ai_viral_label': self.ai_viral_label,
        }
