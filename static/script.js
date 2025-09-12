document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const galleryGrid = document.getElementById('gallery-grid');
    const loader = document.getElementById('loader');
    const modalOverlay = document.getElementById('modal-overlay');
    const modalImg = document.getElementById('modal-img');
    const modalOwner = document.getElementById('modal-owner');
    const modalDate = document.getElementById('modal-date');
    const modalTags = document.getElementById('modal-tags');
    const modalDownloadBtn = document.getElementById('modal-download');
    const modalCopyLinkBtn = document.getElementById('modal-copy-link');
    const modalFindSimilarBtn = document.getElementById('modal-find-similar');
    const modalCloseBtn = document.getElementById('modal-close');

    let currentResults = [];

    const performSearch = async (query = '') => {
        galleryGrid.innerHTML = '';
        loader.classList.remove('loader-hidden');

        try {
            const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            currentResults = await response.json();
            renderImages(currentResults);
        } catch (error) {
            console.error('Search failed:', error);
            galleryGrid.innerHTML = '<p class="error-message">Search failed. Please try again later.</p>';
        } finally {
            loader.classList.add('loader-hidden');
        }
    };

    const renderImages = (images) => {
        if (!images || images.length === 0) {
            galleryGrid.innerHTML = '<p class="error-message">No images found matching your query.</p>';
            return;
        }

        const fragment = document.createDocumentFragment();
        images.forEach(image => {
            const card = document.createElement('div');
            card.className = 'gallery-card';
            card.dataset.id = image.id;
            
            const img = document.createElement('img');
            img.src = image.Url;
            img.alt = `By ${image.owner}: ${image.Tags.join(', ')}`;
            img.loading = 'lazy';
            
            card.appendChild(img);
            fragment.appendChild(card);
        });
        galleryGrid.appendChild(fragment);
    };

    const openModal = (imageId) => {
        const image = currentResults.find(img => img.id === imageId);
        if (!image) return;

        modalImg.src = image.Url;
        modalOwner.textContent = image.owner;
        modalDate.textContent = new Date(image.timestamp).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
        
        modalTags.innerHTML = image.Tags.map(tag => `<span>#${tag}</span>`).join('');
        
        modalDownloadBtn.dataset.url = image.Url;
        modalCopyLinkBtn.dataset.url = image.Url;
        modalFindSimilarBtn.dataset.tags = image.Tags.join(' OR ');

        modalOverlay.classList.remove('modal-hidden');
        document.body.style.overflow = 'hidden';
    };

    const closeModal = () => {
        modalOverlay.classList.add('modal-hidden');
        document.body.style.overflow = 'auto';
    };

    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        performSearch(searchInput.value.trim());
    });

    galleryGrid.addEventListener('click', (e) => {
        const card = e.target.closest('.gallery-card');
        if (card && card.dataset.id) {
            openModal(card.dataset.id);
        }
    });
    
    modalCloseBtn.addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) closeModal();
    });

    modalDownloadBtn.addEventListener('click', async (e) => {
        const url = e.currentTarget.dataset.url;
        try {
            const response = await fetch(url);
            const blob = await response.blob();
            const objectUrl = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = objectUrl;
            a.download = url.split('/').pop() || 'image.jpg';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(objectUrl);
        } catch (error) {
            console.error('Download failed:', error);
            window.open(url, '_blank');
        }
    });

    modalCopyLinkBtn.addEventListener('click', (e) => {
        navigator.clipboard.writeText(e.currentTarget.dataset.url).then(() => {
            e.currentTarget.textContent = 'Copied!';
            setTimeout(() => { e.currentTarget.textContent = 'Copy Link'; }, 2000);
        });
    });
    
    modalFindSimilarBtn.addEventListener('click', (e) => {
        const tagsQuery = e.currentTarget.dataset.tags;
        closeModal();
        searchInput.value = tagsQuery;
        performSearch(tagsQuery);
    });

    performSearch();
});
