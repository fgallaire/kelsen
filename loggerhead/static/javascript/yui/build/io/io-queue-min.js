/*
Copyright (c) 2008, Yahoo! Inc. All rights reserved.
Code licensed under the BSD License:
http://developer.yahoo.net/yui/license.txt
version: 3.0.0pr2
*/
YUI.add("io-queue",function(B){var A=[],K=1,C=false;function I(L,N){if(C===false||A.length<C){var M=B.io._id();A.push({uri:L,id:M,cfg:N});}else{return false;}if(K===1){F();}return M;}function D(O){var M;for(var L=0;L<A.length;L++){if(A[L].id===O){M=A.splice(L,1);var N=A.unshift(M[0]);break;}}}function F(){var L=A.shift();B.io(L.uri,L.cfg,L.id);}function J(L){if(L){C=L;return L;}else{return A.length;}}function E(){var L=(A.length>C>0)?C:A.length;if(L>1){for(var M=0;M<L;M++){F();}}else{F();}}function H(){K=0;}function G(M){if(B.Lang.isNumber(M)){for(var L=0;L<A.length;L++){if(A[L].id===M){A.splice(L,1);break;}}}}I.size=J;I.start=E;I.stop=H;I.promote=D;I.purge=G;B.mix(B.io,{queue:I,},true);},"3.0.0pr2",{requires:["io-base"]});