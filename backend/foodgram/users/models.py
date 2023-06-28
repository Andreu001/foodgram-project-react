from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator


class User(AbstractUser):
    """Модель пользователя"""
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        blank=False
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        blank=False
    )
    email = models.EmailField(
        verbose_name='Email',
        max_length=254,
        unique=True
    )
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        verbose_name='Username',
        max_length=150,
        unique=True,
        validators=[username_validator]
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['-pk']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
