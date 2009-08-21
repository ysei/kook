# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright$
### $License$
###


package Kook::Cookbook;
use strict;
use Data::Dumper;

use Kook::Utils;
use Kook::Sandbox;
use Kook::Misc ('_debug', '_trace');


sub new {
    my ($class, $bookname, $properties) = @_;
    my $this = {
        bookname              => $bookname,
        specific_task_recipes => [],
        generic_task_recipes  => [],
        specific_file_recipes => [],
        generic_task_recipes  => [],
        materials             => [],
        property_names        => [],
        _property_names_dict  => undef,
        context               => undef,
    };
    $this = bless $this, $class;
    $this->load_file($bookname, $properties) if $bookname;
    return $this;
}

sub prop {
    my ($this, $name, $value) = @_;
    my $found;
    if (! exists $this->{_property_names_dict}->{$name}) {
        $this->{_property_names_dict}->{$name} = 1;
        push @{$this->{property_names}}, $name;
    }
    if (exists $this->{context}->{$name}) {
        $value = $this->{context}->{$name};
    }
    else {
        $this->{context}->{$name} = $value;
    }
    return $value;
}

sub all_properties {
    my ($this) = @_;
    my @tuples;
    for (@{$this->{property_names}}) {
        push @tuples, [$_, $this->{context}->{$_}];
    }
    return \@tuples;
}

sub default_product {
    my ($this) = @_;
    #return $this->{context}->{kook_default_product};
    return $Kook::default_product;
}

sub load_file {
    my ($this, $filename, $properties) = @_;
    $this->{bookname} = $filename;
    -f $filename  or die "$filename: not found.\n";
    my $content = Kook::Utils::read_file($filename);
    $this->load($content, $filename, $properties);
}

sub load {
    my ($this, $content, $bookname, $properties) = @_;
    $bookname = '(kook)' if ! $bookname;
    #my $context = $this->create_context();
    my $context = {};
    ## merge hash
    if ($properties) {
        for my $k (keys %$properties) {
            $context->{$k} = $properties->{$k};
        }
    }
    #python: context['prop'] = self.prop
    $this->{context} = $context;
    $Kook::all_recipes = [];
    Kook::Sandbox::_eval($content, $bookname, $context);
    ! $@  or die("[ERROR] kookbook has error:\n$@\n");
    ## masks
    my $TASK     = 0x0;
    my $FILE     = 0x1;
    my $SPECIFIC = 0x0;
    my $GENERIC  = 0x2;
    ## create recipes
    my $recipes = [
        [],    # SPECIFIC | TASK
        [],    # SPECIFIC | FILE
        [],    # GENERIC  | TASK
        [],    # GNERIC   | FILE
    ];
    ## TODO: materials
    for my $recipe (@$Kook::all_recipes) {
        my $flag = $recipe->{kind} eq 'task' ? $TASK : $FILE;
        $flag = $flag | ($recipe->{pattern} ? $GENERIC : $SPECIFIC);
        push @{$recipes->[$flag]}, $recipe;
    }
    $this->{specific_task_recipes} = $recipes->[$SPECIFIC | $TASK];  ## TODO: use dict
    $this->{specific_file_recipes} = $recipes->[$SPECIFIC | $FILE];  ## TODO: use dict
    $this->{generic_task_recipes}  = $recipes->[$GENERIC  | $TASK];  ## TODO: support priority
    $this->{generic_file_recipes}  = $recipes->[$GENERIC  | $FILE];  ## TODO: support priority
    Kook::Misc::_trace("specific task recipes: ", Dumper($this->{specific_task_recipes}));
    Kook::Misc::_trace("specific file recipes: ", Dumper($this->{specific_file_recipes}));
    Kook::Misc::_trace("generic  task recipes: ", Dumper($this->{generic_task_recipes}));
    Kook::Misc::_trace("generic  file recipes: ", Dumper($this->{generic_file_recipes}));
}

sub material_p {
    my ($this, $target) = @_;
    for my $item (@{$this->{materials}}) {
        return 1 if $item eq $target;
    }
    return 0;
}

sub find_recipe {
    my ($this, $target) = @_;
    my $recipes_tuple = [
        $this->{specific_task_recipes},
        $this->{specific_file_recipes},
        $this->{generic_task_recipes},
        $this->{generic_file_recipes},
    ];
    for my $recipes (@$recipes_tuple) {
        for my $recipe (@$recipes) {
            if ($recipe->match($target)) {
                _debug("Cookbook#find_recipe(): target=$target, func=$recipe->{name}, product=$recipe->{product}", 2);
                return $recipe;
            }
        }
    }
}


1;
