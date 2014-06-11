(function ($) {
    'use strict';

    $(function() {

	window.getCookie = function(name){
	    var cookieValue = null;
	    if (document.cookie && document.cookie != '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
		    var cookie = $.trim(cookies[i]);
		    // Does this cookie string begin with the name we want?
		    if (cookie.substring(0, name.length + 1) == (name + '=')) {
			cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
			break;
		    }
		}
	    }
	    return cookieValue;
	}

	window.csrfSafeMethod = function(method){
	    // these HTTP methods do not require CSRF protection
	    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
	}

	window.sameOrigin = function(url){
	    // test that a given url is a same-origin URL
	    // url could be relative or scheme relative or absolute
	    var host = document.location.host; // host + port
	    var protocol = document.location.protocol;
	    var sr_origin = '//' + host;
	    var origin = protocol + sr_origin;
	    // Allow absolute or scheme relative URLs to same origin
	    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
		(url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
		// or any other URL that isn't scheme relative or absolute i.e relative.
		!(/^(\/\/|http:|https:).*/.test(url));
	}

	$.ajaxSetup({
	    beforeSend: function(xhr, settings) {
		if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
		    // Send the token to same-origin, relative URLs only.
		    // Send the token only if the method warrants CSRF protection
		    // Using the CSRFToken value acquired earlier
		    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
		}
	    }
	});


	if (typeof String.prototype.startsWith != 'function') {
	    String.prototype.startsWith = function (str){
		return this.indexOf(str) == 0;
	    };
	}
	if (typeof String.prototype.endsWith != 'function') {
	    String.prototype.endsWith = function(suffix) {
		return this.indexOf(suffix, this.length - suffix.length) !== -1;
	    };
	}

	/* Init the graph view if we have graph-view preview boxes */
	if($('.iobject-graph').length > 0){
	    $.each($('.iobject-graph'), function(){
		var graph_box = $(this),
		    graph_canvas = graph_box.find('.iobject-graph-canvas').first();
		
		


		// Callback function for rendering graph/graph
		var render_graph = function(gdata){

		    // If we do not have any nodes, don't draw.
		    if(gdata.nodes.length == 0)
			return;

		    graph_box.toggle(); // Show the box. Needed to get the canvas dimensions

		    var nodes = {},
		        links = [],
		        width = graph_canvas.width(),
		        height  = graph_canvas.height(),
		        duration = 300,
		        root_id = gdata.node_id,
		        linkedByIndex = {},
		        self_index = 0;


		    // Compute the nodes and the links.
		    $.each(gdata.nodes, function(i,v){
			nodes[v[0]] = v[1];
			nodes[v[0]]['id'] = v[0];
			if(v[0]==root_id)
			    nodes[v[0]]['fixed'] = true;
		    });
		    $.each(gdata.edges, function(i,v){
			links.push({
			    source: nodes[v[0]],
			    target: nodes[v[1]],
			    meta: v[2]
			});
			linkedByIndex[v[0] + ',' + v[1]] = 1;
		    });

		    function isConnected(a, b) {
			return linkedByIndex[a.id + "," + b.id] || linkedByIndex[b.id + "," + a.id] || a.id == b.id;
		    }


		    var svg = d3.select(graph_canvas.get(0))
			.append("svg:svg")
		    	  .attr("width", width)
			  .attr("height", height)
			  .attr("pointer-events", "all")
		    	.append("svg:g")
			  .call(d3.behavior.zoom().on("zoom", zoom))
			.append('svg:g');

		    svg.append('svg:rect')
			.attr('width', 2*width)
			.attr('height', 2*height)
			.attr('fill', 'white')
			.attr('transform', 'translate(' + (-width/2) + ',' + (-height/2) + ')');

		    svg.append("svg:defs").selectAll("marker")
			.data(["end"])
			.enter().append("svg:marker")
			.attr("id", String)
			.attr("viewBox", "0 -5 10 10")
			.attr("refX", 21)
			.attr("refY", 0)
			.attr("markerWidth", 5)
			.attr("markerHeight", 5)
			.attr("orient", "auto")
			.append("svg:path")
			.attr("d", "M0,-5L10,0L0,5");

		    function zoom() {
			svg.attr("transform",
				 "translate(" + d3.event.translate + ")"
				 + " scale(" + d3.event.scale + ")");
			svg.selectAll('.toggle-hover').attr('transform', 'scale('+ 1/d3.event.scale +')')
		    }


		    var force = d3.layout.force()
			.nodes(d3.values(nodes))
			.links(links)
			.size([width, height])
			.linkDistance(25)
			.charge(-1500)
			.on("tick", tick)
			.size([width, height]);


		    var link = svg.selectAll(".link")
			.data(force.links())
			.enter().append("path")
			.attr("class", "link")
			.attr('marker-end', 'url(#end)');

		    var node = svg.selectAll(".node")
			.data(force.nodes())
			.enter().append("g")
			.attr("class", "node")
			.each(function(d, i) {
			    var t = d3.select(this);
			    var t_core = false;

			    // Do we have image info attached to the node?
			    if(d.image){
				t_core = t.append("image");
				$.each(d.image, function(di, dv){
				    t_core.attr(di, dv);
				});
			    }else{ // No image, show a plain circle
				t_core = t.append("circle")
				    .attr("r", 10);
			    }

			    t_core.on('mouseover', fade(.3, 'over'))
				.on('mouseout', fade(1, 'out'))
				.on('click', node_click);

			    t.append('rect')
			    	.attr('class', 'toggle-hover')
			    	.attr('height' , '14px')
			    	.attr('fill', '#ddd')
		    	    	.attr("x", 10)
			    	.attr("opacity", "0");
			    
			    t.append("text")
			    	.attr("class", "toggle-hover")
		    	    	.attr("x", 12)
			    	.attr("y", 7)
		    	    	.attr("dy", ".35em")
			    	.attr("opacity", "0")
		    	    	.text(function(d) { return d.name; });

			    if(d.fixed){
				self_index = i;
				t_core = t.insert("circle", ":first-child")
				    .attr("r", 15)
				    .attr('style', 'fill:red;stroke-width:0;')
				    .attr('opacity', '.3');
			    }
			});

		    function node_click(e){
			var el = $('.iobject-graph .details-box').first(),
			    img = $(this).attr('href');

			
			el.find('.title').text(e.iobject_type + ': ' + e.name);
			el.find('img').attr('src', img);
			var itmpl = '<table><tbody> \
			      <tr><td>NS:</td> <td>'+ e.identifier_ns +'</td></tr> \
			      <tr><td>ID:</td> <td>'+ e.identifier_uid +'</td></tr> \
			      <tr><td>Link:</td> <td><a href="'+ e.url +'">'+ e.id +'</a></td></tr> \
			      </tbody></table> \
                        ';
			el.find('.desc').html(itmpl);

			el.find('.ui-icon-close').click(function(){
			     $(this).parent().hide();
			});

			el.show();
		    }


		    function fade(opacity, oo) {
			return function(d) {
			    node.style("stroke-opacity", function(o) {
				var thisOpacity = isConnected(d, o) ? 1 : opacity;

				if(oo=='out' && isConnected(d, o)){
				    d3.select(this).selectAll('.toggle-hover')
					.attr('opacity', '0')
					.attr('stroke-opacity', '0')
					.attr('fill-opacity', '0');

				}
				if(oo=='over' && isConnected(d, o)){
				    d3.select(this).selectAll('.toggle-hover')
					.attr('opacity', '1')
					.attr('stroke-opacity', '1')
					.attr('fill-opacity', '1');

				    // fix the rect backround of the text label
				    var lbl = d3.select(this).selectAll('text.toggle-hover')[0].pop();
				    d3.select(this).selectAll('rect.toggle-hover')
					.attr('width', function(){
					    if(lbl.getBBox().width > 0)
						return lbl.getBBox().width + 5
					    return 0;
					});
				    

				}

 				this.setAttribute('fill-opacity', thisOpacity); //element itself
				d3.select(this).selectAll('image').attr('opacity', thisOpacity);
				return thisOpacity;
			    });

			    link.style("opacity", function(o) {
				return o.source === d || o.target === d ? 1 : opacity;
			    });

			};
		    }


		    function tick(e) {
			// Gravity?
			// var kx = .4 * e.alpha, ky = 1.4 * e.alpha;
			//     links.forEach(function(d, i) {
			//       d.target.x += (d.source.x - d.target.x) * kx;
			//       d.target.y += (d.source.y + 80 - d.target.y) * ky;
			//     });

			node.attr("transform", function(d) { 
			    
			    if(d.index==self_index){
				d.x = width/2;
				d.y = height/2;
			    }

			    var r = d.name.length;
			    //these setting are used for bounding box, see [http://blockses.appspot.com/1129492][1]
			    d.x = Math.max(r, Math.min(width - r, d.x));
			    d.y = Math.max(r, Math.min(height - r, d.y));

			    return "translate("+d.x+","+d.y+")";            

			});

        		link.attr("d", function(d) {
			    var dx = d.target.x - d.source.x,
			    dy = d.target.y - d.source.y;
			    return "M" + d.source.x + "," + d.source.y + " " + d.target.x + "," + d.target.y;
			});

		    }

		    force.start();
		    for(var i=0; i<300; i++){
		    	force.tick();
		    }
		    force.stop();
		    
		}; // End render_graph()



		// Load graph data from backend
		$.getJSON('graph', function(data){
		    if(data.status){
			// Set title of graph box
			$('h2', graph_box).text(data.msg);
			render_graph(data.data);
		    }else{
			//Error fetching graph data
		    }
		});

	    });
	}

    });
}(django.jQuery)); // Reuse django injected jQuery library
