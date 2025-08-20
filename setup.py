#!/usr/bin/env python3
"""
Setup script for Unified Qren Discord Bot
"""

from setuptools import setup, find_packages

setup(
    name="unified-qren-bot",
    version="2.0.0",
    description="Unified Discord Bot System for Arabic Communities",
    author="Qren Development Team",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "discord.py==2.3.2",
        "aiofiles==23.2.1", 
        "aiohttp==3.9.1",
        "beautifulsoup4==4.12.2",
        "flask==3.0.0",
        "psutil==5.9.6",
        "requests==2.31.0",
        "trafilatura==1.8.0"
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)