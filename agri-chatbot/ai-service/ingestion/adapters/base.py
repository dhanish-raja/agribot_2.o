class BaseAdapter:
    def can_handle(self, url):
        return False
    
    def process(self, url, raw_doc):
        # Return segments and images
        return [], []
