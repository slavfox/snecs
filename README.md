# snecs (work in progress)
### A Straightforward, Nimble ECS for Python.

snecs is a pure-Python [ECS] library, heavily inspired by Rust's [Legion], and
aiming to be as fast and easy-to-use as possible with pure Python.

The goal is outrunning [esper].


- [ ] Components
  - [ ] Automatic serialization
- [ ] World
  - [ ] Entity management
  - [ ] Entity cache
  - [ ] Queries
  
  - [ ] [Legion]-inspired filtering
    - [x] Filter builder
          
      Allows building arbitrary filters using simple Python syntax, eg.
      ```python
      world.query(Position).filter(Velocity & ~(Frozen | Static))
      ```
    - [ ] Filter compiler
    
      A full-fledged [Quine-McCluskey] logic minimizer, to precompile filters
      into optimalform, because I hate my life. 
    
    


## License

snecs is made available under the terms of the Mozilla Public License Version 
2.0, the full text of which is available [here], and included in [LICENSE].
If you have questions about the license, check Mozilla's [MPL FAQ].

[ECS]: https://en.wikipedia.org/wiki/Entity_component_system
[Legion]: https://github.com/TomGillen/legion
[esper]: https://github.com/benmoran56/esper
[Quine-McCluskey]: https://en.wikipedia.org/wiki/Quine%E2%80%93McCluskey_algorithm
[here]: https://www.mozilla.org/en-US/MPL/2.0/
[LICENSE]: ./LICENSE
[MPL FAQ]: https://www.mozilla.org/en-US/MPL/2.0/FAQ/
