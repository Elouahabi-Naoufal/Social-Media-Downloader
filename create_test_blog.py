from app import app, db
from utils import Blog

with app.app_context():
    # Create a test blog post
    test_blog = Blog(
        title="Welcome to Our Blog",
        slug="welcome-to-our-blog",
        content="<p>This is our first blog post! Here you'll find tips and tutorials about social media downloading.</p><p>Stay tuned for more content!</p>",
        excerpt="Welcome to our blog where we share tips about social media downloading.",
        published=True
    )
    
    db.session.add(test_blog)
    db.session.commit()
    print("Test blog post created successfully!")