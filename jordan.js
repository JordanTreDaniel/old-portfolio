$(document).ready(()=> {
  //Start typing your code here
  showSkills();
  showEvents();
  $('#next-skill').click(()=> {
    skillsIndex++;
    showSkills();
  });

});

//The index to control the skills section's content
var skillsIndex = 0;
//This function allows me to dynamically add/populate a skills section to the page
function showSkills() {
  //Clear any existing children
  $('#skills-div').empty();
  //Let the index rotate all the way around
  if (skillsIndex === skills.length) {
    skillsIndex = 0;
  }
  //Select the skills div and add the image div
  $('#skills-div').append('<div class="col-xs-4"><img class="skills-image" src="' + skills[skillsIndex].imageUrl + '"></div>');
  //add the text div
  $('#skills-div').append('<div class="col-xs-8"><h4>' + skills[skillsIndex].name + '</h4><p>' + skills[skillsIndex].description + '</p></div>')
}
var skills = [
  {
    name: "Github",
    imageUrl: 'http://hammerjs.github.io/assets/img/github-icon.png',
    description: "I learned about Github when I was still applying for bootcamps, and I've been using it for over a year now. I would say that my skills with github are intermediate, since I know all about pull requests, branches, and cloning!",
  },
  {
    name: "Angular 1.5",
    imageUrl: "",
    description: "I learned how to make a single page app with Angular while in Coder Camps, Nov. '16 - Jan. '17. I am still working with Angular, in particular I am teaching myself how to make a component based application."
  },
  {
    name: "Angular Material",
    imageUrl: "",
    description: "I loved bootstrap, until I met Material Design. This is another skill that I picked up in bootcamp, and it is my favorite design framework. I use it on any project that I get the chance to use it on."
  },
  {
    name: "HTML5",
    imageUrl: "",
    description: "I taught myself to write HTML on Codecademy back in 2015, and I have been practicing it ever since. I have a very good grasp on HTML and the DOM."
  },
  {
    name: "CSS",
    imageUrl: "",
    description: "I learned HTML and CSS simultaneously, and while I definitely prefer using a design framework, I defi"
  },
  {
    name: "JQuery",
    imageUrl: "",
    description: "I learned JQuery as my first javascript framework. That is how I learned to manipulate the DOM and everything. This portfolio was written using JQuery."
  },
  {
    name: "JSON Web Tokens",
    imageUrl: "",
    description: "I learned how to use JWT's during my time in bootcamp as part of my authentication for my projects."
  },
  {
    name: "Express",
    imageUrl: "",
    description: "Express was a big part of my back-end for What's Inside and Coding Skills. I am by no means an expert on this technology, but I remember how to use it to create a basic CRUD API, and how to use it for the main server."
  },
  {
    name: "Node",
    imageUrl: "",
    description: "Node is another technology that I know just enough to use it. I have a basic understanding of how it works now, and I read up on the concepts whenever I can."
  },
  {
    name: "AJAX/HTTP Requests",
    imageUrl: "",
    description: "I have used ajax calls in many different forms, including the JQuery and Angular formats. I have a good solid understanding of how they work and when to use them."
  },
  {
    name: "Typescript",
    imageUrl: "",
    description: "I have been using Typescript for a few months now, which means I am familiar with ES6 code as well. I love the syntax and ease of the language and I cannot wait until ES6 is supported throughout all browsers."
  },
  {
    name: "Mongo/MongoDB",
    imageUrl: "",
    description: "I learned these two technologies almost simultaneously. Mongo is the first DB that I worked with, and I loved the flexibility of the non-relational DB. Although I worked with it for a short period of time, I got pretty good at using it."
  }
]

var timelineIndex = 0;
//Function to populate the timeline section
function showEvents() {
  $('#timeline-div').empty();
  if(timelineIndex === lifeStory.length) {
    timelineIndex = 0;
  }
  //add the event name and date
  var eventHead = lifeStory[timelineIndex].event + ' - ' + lifeStory[timelineIndex].when;
  $("#timeline-div").append('<h5 class="pull-left">' + eventHead + '</h5>')
  //Add the description
  $('#timeline-div').append('<h3 class="pull-right">' + lifeStory[timelineIndex].description + '</h3>');
}
var lifeStory = [
  {
    event: "Birth",
    when: "May 18th, 1993",
    description: "I was born to Jean Marie Christley in Houston, Texas."
  },
  {
    event: "Early Hints",
    when: "2004-2007",
    description: "I think the biggest hint that I would get into software was how much I loved chess from an early age. Despite that, I remember two times in my childhood where people predicted that I would get into computers and I actually got mad because I thought that that made me a geek. Later, when I was 17, I told a judge that I wanted to work on artificial intelligence when she asked me if I wanted to anything with myself. I meant that."
  },
  {
    event: "Growing up",
    when: "1993-2011",
    description: "I lived in many different cities growing up, but I am thankful for that because it taught me to appreciate, and it made me a very cultured, diverse, and accepting person."
  },
  {
    event: "My First Coding Class",
    when: "Early 2015",
    description: "I was pursuing an Associate's in Computer Science at Houston Community College when I took my first coding class in C++. Showing my professor my verion of Hangman, she suggested that I make a career out of coding."
  },
  {
    event: "What's a Coding Bootcamp?",
    when: "Summer 2015",
    description: "I always just assumed the way to get into software was going to college for four years. I wish I had looked earlier. I wish I looked up the sign for The Iron Yard that I always said I would look up. But I'm glad I came across an ad for App Academy on Facebook one day."
  },
  {
    event: "Self Teaching",
    when: "Summer 2015-Summer 2016",
    description: "I would study any time that I could get to a computer. I studied so hard for the admissions, and started preparing so much, before I knew it I had taught myself Ruby, JS, HTML, CSS, Bootstrap, JQuery, and the command line on Codecademy and FreeCodeCamp. I wasted/spent time debating, changing my mind, and preparing for different bootcamps. I was going to do iOS dev after I had already taught myself the web techs, so I started doing pre-work for Flatiron online. I changed my mind. I applied to the Coding House in California, and after completing all challenges and interviews, I was accepted, but then thrown to the side because of my background."
  },
  {
    event: "Coder Camps",
    when: "Late 2016",
    description: "I tried to continue self-teaching, but decided on attending a bootcamp instead. I had to stay local because of my finances. I knew this was it, if I didn't get into a bootcamp by the end of 2016, I may never. I completed the MEAN stack remote program in January 2017."
  },
  {
    event: "Current",
    when: "2017",
    description: "I am self-teaching again, although on a higher level. I am currently looking for a job and trying to become the best develper that I can be."
  }

]
