import { Component, Input, OnInit } from '@angular/core';

import * as d3 from 'd3';

@Component({
  selector: 'workflow',
  styles: [`
  .pane {
    padding: 1em;
  }

  .graph-container {
    width: 100%;
    min-height: calc(100vh - 100px);
  }

  .fill {
    min-height: calc(100vh - 100px);
  }

  svg {
    border: 1px solid #ddd;
  }
  `],
  templateUrl: './workflow.component.html'
})
export class WorkflowComponent implements OnInit{
  @Input() processes: string[];

  drag: boolean;
  dragValue: string;

  nodes: string[];

  ngOnInit() {
    this.nodes = [];

    d3.select('svg')
      .on('mouseover', () => {
        if (this.drag) {
          let origin = d3.mouse(d3.event.target);

          this.nodes.push(this.dragValue);

          let g = d3.select('svg')
            .selectAll('g')
            .data(this.nodes)
            .enter()
              .append('g')
              .attr('transform', `translate(${origin[0]}, ${origin[1]})`)
              .attr('data-toggle', 'modal')
              .attr('data-target', '#configure');

          g.append('circle')
            .attr('r', 60)
            .attr('stroke', 'black')
            .attr('fill', 'white');

          g.append('text')
            .attr('text-anchor', 'middle')
            .text((d) => { return d });

          d3.select('svg')
            .selectAll('g')
            .call(d3.drag()
              .on('drag', function() {
                d3.select(this)
                  .attr('transform', `translate(${d3.event.x}, ${d3.event.y})`);
              })
            );

          this.drag = false;
        }
      });
  }

  dropped(event: any) {
    this.drag = true;
    this.dragValue = event.dragData;
  }
}
