functor
   import System
define

proc {Browse Message}
   {System.showInfo Message}
end

% Wait does not wait infinitely.
% It is used because if the students don't use Browse, it will raise a useless warning.
{Wait Browse}

proc {PrintHello}
   @@q1@@
end

{PrintHello}

end
