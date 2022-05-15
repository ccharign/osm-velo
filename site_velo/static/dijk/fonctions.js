
var compteur = 0;

function gèreLesClics(){
    laCarte.on("click", addMarker);
}


function addMarker(e) {
    // Add marker to map at click location
    //console.log("addMarker lancé");
    compteur+=1;
    
    //const markerPlace = document.querySelector(".marker-position");
    //markerPlace.textContent = `new marker: ${e.latlng.lat}, ${e.latlng.lng}`;

    const marker = new L.marker( e.latlng, {
	draggable: true
    })
	  .bindTooltip(""+compteur, {permanent: true, direction:"bottom"})
	  .addTo(laCarte)
	  .bindPopup(buttonRemove);
    
    marker.numéro = compteur;

    // var marker = L.marker(props.coords,
    // 			  {icon: myIcon}).bindTooltip(props.country, {permanent: true, direction : 'bottom'}
    // 						     ).addTo(mymap);


    // event remove marker
    marker.on("popupopen", removeMarker);

    // event draged marker
    marker.on("dragend", dragedMarker);

    form = document.getElementById("relance_rapide");
    addHidden(form, "étape_coord"+compteur, e.latlng.lng +";"+ e.latlng.lat)
    
}

const buttonRemove =
  '<button type="button" class="remove">Supprimer</button>';

// remove marker
function removeMarker() {
    
    const marker = this;
    const btn = document.querySelector(".remove");
    
    btn.addEventListener("click", function () {
	const markerPlace = document.querySelector(".marker-position");
	//markerPlace.textContent = "goodbye marker";
	hidden = document.getElementById("étape_coord"+marker.numéro);
	hidden.remove()
	laCarte.removeLayer(marker);
    });
}

// draged
function dragedMarker() {
  //const markerPlace = document.querySelector(".marker-position");
  //markerPlace.textContent = `change position: ${this.getLatLng().lat}, ${
  //  this.getLatLng().lng
    //}`;
    const marker=this;
    document.getElementById("étape_coord"+marker.numéro).value = marker.getLatLng().lat+";"+ marker.getLatLng().lng;
}

function addHidden(theForm, key, value) {
    // Create a hidden input element, and append it to the form:
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = key; // 'the key/name of the attribute/field that is sent to the server
    input.value = value;
    input.id = key;
    theForm.appendChild(input);
}
