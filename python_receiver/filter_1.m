function y = filter_1(in)
    Hd = elliptic_iir_bandpass_8000;

    y = Hd.filter(in);
end