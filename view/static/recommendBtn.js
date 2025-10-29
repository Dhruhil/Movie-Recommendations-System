//recommend

function reactivateModal() {

    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());

    const modal = document.getElementById('movieDetailsModal');
    modal.classList.add('fade');
    modal.setAttribute('aria-hidden', 'true');
    modal.style.display = ''; // Reset display to default
}

function deactivateModal() {
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());

    const modal = document.getElementById('movieDetailsModal');
    modal.classList.remove('fade');
    modal.setAttribute('aria-hidden', 'false');
    modal.style.display = 'none'; // Hide the modal
}


document.addEventListener('DOMContentLoaded', function () {






  const recommendBtn = document.getElementById('recommendBtn');
  
  recommendBtn.addEventListener('click', function () {
    // Replace the button with a spinner
    recommendBtn.innerHTML = `
      <div class="spinner-grow text-primary" style="width: 3rem; height: 3rem;" role="status">
        <span class="sr-only"></span>
      </div>`;
    recommendBtn.disabled = true; // Disable the button to prevent multiple clicks

    // Gather all widgets in the dashboard
    const widgets = document.querySelectorAll('#advanced-grid .grid-stack-item');

    // Extract metadata from each widget
    const allMetadata = Array.from(widgets).map(widget => {
      return JSON.parse(widget.getAttribute('data-meta'));
    });

    // Send data to the server
    fetch('/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ allMetadata }),
    })
      .then(response => response.json())
 .then((data) => {
          reactivateModal();
          console.log('Recommendation Response:', data);

          // Extracting data
          const recommendedMovies = data;

          // Define the parent container for widgets
          const recommendationContent = document.getElementById('recommendationContent');
          recommendationContent.innerHTML = ''; // Clear existing content if any

          // Create movie widgets for each entry
          recommendedMovies.forEach((movie, index) => {
              // Metadata is already mapped within each recommended movie
              const metadata = movie.metadata || {};

              const pointBreakdown = movie.point_breakdown || metadata.point_breakdown || {}; // huh

              // Fallback poster if not found in metadata
              const poster = metadata.poster || 'https://via.placeholder.com/300';

              // IMDb rating or fallback to provided ratings
              const imdbRating = metadata.imdb_ratings || metadata.ratings || 'N/A';

              // Generate the widget HTML
              const widgetHTML = `
                  <div class="grid-stack-item draggable-widget newWidget" style="
                      background-image: url('${poster}');
                      background-size: cover; 
                      background-position: center;
                      overflow: visible; /* Ensure content outside is visible */
                      position: relative;" 
                      gs-w="3" gs-h="5" 
                      data-meta="${encodeURIComponent(JSON.stringify({
                          imdb: metadata.imdb || null,
                          imdb_ratings: imdbRating,
                          media_type: metadata.media_type || 'unknown',
                          name: movie.title || 'Unknown',
                          popularity: metadata.popularity || 0,
                          backdrop: metadata.backdrop,
                          overview: metadata.overview,
                          point_breakdown: pointBreakdown,
                          poster: poster,
                          ratings: metadata.ratings || 0,
                          score: movie.points,
                          uri: movie.movie_uri
                      }))}"
                      gs-x="3" gs-y="1">
                      
                      <!-- Ranking Number -->
                      <div style="
                          position: absolute;
                          top: -20px; /* Move further outside */
                          left: -20px; /* Adjust left margin */
                          font-size: 32px; /* Bigger number */
                          font-weight: bold;
                          color: #ff4757;
                          z-index: 10;
                          transform: rotate(-15deg);"
                          title="Rank">
                          ${index + 1}
                      </div>

                      <div class="widget-title-bar">${movie.title || 'Unknown'}</div>

                      <!-- Rating Banner -->
                      <div style="
                          position: absolute;
                          top: 0;
                          right: 0;
                          width: 35px;
                          height: 50px;
                          background-color: #f1c40f;
                          color: black;
                          display: flex;
                          align-items: flex-start;
                          justify-content: center;
                          font-weight: bold;
                          font-size: 14px;
                          clip-path: polygon(
                              0% 0%,      /* Top-left corner */
                              100% 0%,    /* Top-right corner */
                              100% 100%,  /* Bottom-right corner */
                              85% 100%,   /* Start in from right edge for wide V */
                              50% 75%,    /* Move up for the inverted V peak */
                              15% 100%,   /* Move in from left edge */
                              0% 100%     /* Bottom-left corner */
                          );
                          z-index: 5;"
                          title="Official IMDb Rating">
                          ${imdbRating}
                      </div>
                  </div>`;

              // Inject the widget into the modal content
              recommendationContent.innerHTML += widgetHTML;
          });

          recommendBtn.innerHTML = 'Recommend';
          recommendBtn.disabled = false;

          // Initialize and show the modal
          const recommendModal = new bootstrap.Modal(document.getElementById('recommendModal'), {});
          recommendModal.show();
          deactivateModal();

          //now fixx so we can clcik the movies for extra info
          document.addEventListener('click', function (e) {
              const movieWidget = e.target.closest('.grid-stack-item');
              if (movieWidget) {
                  const movieMeta = JSON.parse(decodeURIComponent(movieWidget.getAttribute('data-meta')));

                  console.log(movieMeta)
                  // Populate the movie details modal
                  const movieDetailsContent = document.getElementById('movieDetailsContent');

                        if (recommendModal._isShown) {
                            //continue if recommendmodal is shown
                        
                 
                  
                  const pointBreakdown = movieMeta.point_breakdown || {};
                  let breakdownHTML = '<table style="width:100%; border-collapse: collapse;">';
                  breakdownHTML += '<tr><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Category</th><th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Details</th></tr>';

                  // Iterate through point breakdown for detailed insight
                  for (const [key, value] of Object.entries(pointBreakdown)) {
                      breakdownHTML += `<tr>
                          <td style="border: 1px solid #ddd; padding: 8px;">${key}</td>
                          <td style="border: 1px solid #ddd; padding: 8px;">${typeof value === 'object' ? JSON.stringify(value, null, 2).replace(/\n/g, '<br>').replace(/\s/g, '&nbsp;') : value}</td>
                      </tr>`;
                  }
                  breakdownHTML += '</table>';

                  movieDetailsContent.innerHTML = `
                      <div style="position: relative; display: inline-block; max-width: 100%; margin-bottom: 20px;">
                          <img 
                              src="${movieMeta.backdrop || movieMeta.poster || 'https://via.placeholder.com/300'}" 
                              alt="${movieMeta.name || 'Backdrop'}" 
                              style="width: 100%; height: auto; display: block;"
                          >
                          <div style="
                              position: absolute; 
                              bottom: 0; 
                              width: 100%; 
                              background: rgba(0, 0, 0, 0.7); 
                              color: white; 
                              padding: 10px; 
                              box-sizing: border-box;
                          ">
                              <p style="margin: 0;">${movieMeta.overview || 'No overview available.'}</p>
                          </div>
                      </div>
                      <h3>${movieMeta.name || 'Unknown'}</h3>
                      <p><strong>IMDb Rating:</strong> ${movieMeta.imdb_ratings || 'N/A'}</p>
                      <p><strong>Media Type:</strong> ${movieMeta.media_type || 'N/A'}</p>
                      <p><strong>Popularity:</strong> ${movieMeta.popularity || 'N/A'}</p>
                      <p><strong>Score:</strong> ${movieMeta.score || 'N/A'}</p>
                      <p><strong>URI:</strong> <a href="${movieMeta.uri || '#'}" target="_blank">${movieMeta.uri || 'N/A'}</a></p>
                      <p><strong>IMDB:</strong> <a href="https://www.imdb.com/title/${movieMeta.imdb || '#'}" target="_blank">${movieMeta.imdb || 'N/A'}</a></p>
                      <div style="
                          margin-top: 30px; 
                          padding: 15px; 
                          border-radius: 5px; 
                          background: linear-gradient(135deg, #333333, #555555); 
                          color: white; 
                          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                      ">
                          <h3>Recommendation Insight</h3>
                          ${breakdownHTML}
                      </div>        
                  `;

                  // Show the movie details modal
                  const movieDetailsModal = new bootstrap.Modal(document.getElementById('movieDetailsModal'), {});
                  movieDetailsModal.show();
              }
              }
          });

      })
      .catch(err => {
        console.error('Error in /recommend request:', err);

        // Restore the button on error
        recommendBtn.innerHTML = 'Recommend';
        recommendBtn.disabled = false;
        deactivateModal();
      }); // Correct placement of catch
  });
});
