from django.db import models
from accounts.models import User
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

class Project(models.Model):
    name= models.CharField(max_length=225)
    description= models.TextField(blank=True)
    owner= models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_projects")
    members= models.ManyToManyField(User, related_name="projects")
    is_archived= models.BooleanField(default=False)

    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.members.add(self.owner)

    def __str__(self):
        return self.name


@receiver(m2m_changed, sender=Project.members.through)
def enforce_owner_membership(sender, instance, action, reverse, **kwargs):
    # 1. Safety Check: If modifying from the User side (reverse=True),
    # 'instance' is a User, so we skip to avoid crashing.
    if reverse:
        return

    # 2. Logic: Only run on changes that might remove the owner
    if action in ("post_add", "post_remove", "post_clear"):

        # 3. Performance: Use .filter().exists() instead of .all()
        # This checks the DB directly without loading a list of users
        if instance.owner_id and not instance.members.filter(id=instance.owner_id).exists():
            instance.members.add(instance.owner)